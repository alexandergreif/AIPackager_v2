"""API routes for PSADT script generation."""

import time
from typing import Any, Dict, List, Optional

from flask import Blueprint, current_app, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from loguru import logger
from pydantic import BaseModel, ValidationError

from ai_psadt_agent.api.auth import (
    GENERATION_RATE_LIMIT,
    VALIDATION_RATE_LIMIT,
    require_api_key,
)
from ai_psadt_agent.domain_models.package import Package
from ai_psadt_agent.infrastructure.db.session import get_db_session
from ai_psadt_agent.services.prompt_templates import InstallerMetadata
from ai_psadt_agent.services.script_generator import get_script_generator

bp = Blueprint("generation", __name__, url_prefix="/v1")

limiter = Limiter(key_func=get_remote_address)


class GenerationRequest(BaseModel):
    """Request model for script generation."""

    installer_metadata: Dict[str, Any]
    user_notes: Optional[str] = None
    save_to_package: bool = True


class GenerationResponse(BaseModel):
    """Response model for script generation."""

    script_content: str
    validation_score: float
    issues: List[str]
    suggestions: List[str]
    rag_sources: List[str]
    metadata: Dict[str, Any]
    package_id: Optional[int] = None


@bp.route("/generate", methods=["POST"])
@require_api_key
@limiter.limit(GENERATION_RATE_LIMIT)  # type: ignore[misc]
def generate_script() -> Any:  # noqa: C901
    """Generate PSADT script from installer metadata."""
    start_time = time.time()
    metrics = current_app.config.get("METRICS", {})
    endpoint_name = "/v1/generate"

    try:
        data = request.get_json()
        if not data:
            if "generation_counter" in metrics:
                metrics["generation_counter"].labels(status="validation_error").inc()
            return jsonify({"error": "No JSON data provided"}), 400

        try:
            generation_request = GenerationRequest(**data)
        except ValidationError as e:
            if "generation_counter" in metrics:
                metrics["generation_counter"].labels(status="validation_error").inc()
            return jsonify({"error": f"Invalid request data: {str(e)}"}), 400

        installer_data = generation_request.installer_metadata
        required_fields = ["name", "version", "vendor", "installer_type"]
        missing_fields = [field for field in required_fields if field not in installer_data]
        if missing_fields:
            if "generation_counter" in metrics:
                metrics["generation_counter"].labels(status="validation_error").inc()
            return jsonify({"error": f"Missing required installer metadata fields: {', '.join(missing_fields)}"}), 400

        installer_metadata = InstallerMetadata(
            name=installer_data["name"],
            version=installer_data["version"],
            vendor=installer_data["vendor"],
            installer_type=installer_data["installer_type"],
            installer_path=installer_data.get("installer_path"),
            silent_args=installer_data.get("silent_args"),
            uninstall_args=installer_data.get("uninstall_args"),
            architecture=installer_data.get("architecture", "x64"),
            language=installer_data.get("language", "EN"),
            notes=installer_data.get("notes"),
        )

        logger.info(f"Generating script for {installer_metadata.name} v{installer_metadata.version}")
        script_generator = get_script_generator()
        generation_result = script_generator.generate_script(
            installer_metadata=installer_metadata,
            user_notes=generation_request.user_notes,
        )

        if generation_result is None:
            logger.error("generate_script from script_generator returned None, indicating critical failure.")
            if "generation_counter" in metrics:
                metrics["generation_counter"].labels(status="error").inc()
            return jsonify({"error": "Critical script generation failure"}), 500

        package_id = None
        if generation_request.save_to_package:
            try:
                with get_db_session() as session:
                    if "db_operations" in metrics:
                        metrics["db_operations"].labels(operation="create", status="started").inc()
                    db_package = Package(
                        name=installer_metadata.name,
                        version=installer_metadata.version,
                        installer_path=installer_metadata.installer_path,
                        script_text=generation_result.script_content,
                    )
                    session.add(db_package)
                    session.flush()
                    package_id = db_package.id
                    if "db_operations" in metrics:
                        metrics["db_operations"].labels(operation="create", status="success").inc()
                logger.info(f"Saved generated script to package ID: {package_id}")
            except Exception as e:
                logger.error(f"Error saving package to database: {str(e)}")
                if "db_operations" in metrics:
                    metrics["db_operations"].labels(operation="create", status="error").inc()
                pass

        response_data = GenerationResponse(
            script_content=generation_result.script_content,
            validation_score=generation_result.validation_score,
            issues=generation_result.issues,
            suggestions=generation_result.suggestions,
            rag_sources=generation_result.rag_sources,
            metadata=generation_result.metadata,
            package_id=package_id,
        )

        if "generation_counter" in metrics:
            metrics["generation_counter"].labels(status="success").inc()

        duration = time.time() - start_time
        if "generation_duration" in metrics:
            metrics["generation_duration"].labels(endpoint=endpoint_name).observe(duration)

        logger.info(f"Script generation completed with score: {generation_result.validation_score} in {duration:.2f}s")
        return jsonify(response_data.model_dump()), 200

    except Exception as e:
        if "generation_counter" in metrics:
            metrics["generation_counter"].labels(status="error").inc()

        duration = time.time() - start_time
        if "generation_duration" in metrics:
            metrics["generation_duration"].labels(endpoint=endpoint_name).observe(duration)

        logger.error(f"Error during script generation: {str(e)}")
        return jsonify({"error": f"Script generation failed: {str(e)}"}), 500


@bp.route("/validate", methods=["POST"])
@require_api_key
@limiter.limit(VALIDATION_RATE_LIMIT)  # type: ignore[misc]
def validate_script() -> Any:
    """Validate a PSADT script for compliance."""
    try:
        data = request.get_json()
        if not data or "script_content" not in data:
            return jsonify({"error": "script_content is required"}), 400

        script_content = data["script_content"]
        if not script_content.strip():
            return jsonify({"error": "script_content cannot be empty"}), 400

        script_generator = get_script_generator()
        validation_result = script_generator.compliance_linter.validate_script(script_content)
        logger.info(f"Script validation completed with score: {validation_result['score']}")
        return jsonify(validation_result), 200

    except Exception as e:
        logger.error(f"Error during script validation: {str(e)}")
        return jsonify({"error": f"Script validation failed: {str(e)}"}), 500


@bp.route("/status", methods=["GET"])
def generation_status() -> Any:
    """Get status of generation services."""
    try:
        script_generator = get_script_generator()
        llm_provider_name = script_generator.llm_provider.get_provider_name()
        status = {
            "services": {
                "script_generator": "ready",
                "llm_provider": llm_provider_name,
                "compliance_linter": "ready",
            },
            "capabilities": {
                "script_generation": True,
                "script_validation": True,
            },
        }
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Error getting generation status: {str(e)}")
        return jsonify({"error": f"Status check failed: {str(e)}"}), 500
