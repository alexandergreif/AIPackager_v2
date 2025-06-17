from flask import Blueprint, request, jsonify
from loguru import logger

from src.ai_psadt_agent.domain_models.package import (
    Package,
    PackageCreate,
    PackageUpdate,
    PackageResponse,
)
from src.ai_psadt_agent.infrastructure.db.session import get_db_session

bp = Blueprint("packages", __name__, url_prefix="/v1/packages")


@bp.route("", methods=["POST"])
def create_package():
    """Create a new package."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Validate input using Pydantic
        package_data = PackageCreate(**data)

        with get_db_session() as session:
            # Create new package
            db_package = Package(
                name=package_data.name,
                version=package_data.version,
                installer_path=package_data.installer_path,
                script_text=package_data.script_text,
            )
            session.add(db_package)
            session.flush()  # To get the ID

            # Convert to response model while in session
            response_data = PackageResponse.model_validate(db_package)
            response_dict = response_data.model_dump()

            # Store name and version for logging
            package_name = db_package.name
            package_version = db_package.version

        logger.info(f"Created package: {package_name} v{package_version}")
        return jsonify(response_dict), 201

    except Exception as e:
        logger.error(f"Error creating package: {str(e)}")
        return jsonify({"error": str(e)}), 400


@bp.route("/<int:package_id>", methods=["GET"])
def get_package(package_id: int):
    """Get a package by ID."""
    try:
        with get_db_session() as session:
            db_package = session.get(Package, package_id)
            if not db_package:
                return jsonify({"error": "Package not found"}), 404

            response_data = PackageResponse.model_validate(db_package)

        return jsonify(response_data.model_dump()), 200

    except Exception as e:
        logger.error(f"Error getting package {package_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route("", methods=["GET"])
def list_packages():
    """List all packages."""
    try:
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)

        with get_db_session() as session:
            packages = session.query(Package).offset(offset).limit(limit).all()

            response_data = [
                PackageResponse.model_validate(pkg).model_dump() for pkg in packages
            ]

        return jsonify(
            {
                "packages": response_data,
                "total": len(response_data),
                "offset": offset,
                "limit": limit,
            }
        ), 200

    except Exception as e:
        logger.error(f"Error listing packages: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route("/<int:package_id>", methods=["PUT"])
def update_package(package_id: int):
    """Update a package by ID."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Validate input using Pydantic
        package_update = PackageUpdate(**data)

        with get_db_session() as session:
            db_package = session.get(Package, package_id)
            if not db_package:
                return jsonify({"error": "Package not found"}), 404

            # Update only provided fields
            update_data = package_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_package, field, value)

            session.flush()
            response_data = PackageResponse.model_validate(db_package)
            response_dict = response_data.model_dump()

            # Store for logging
            package_name = db_package.name
            package_version = db_package.version

        logger.info(f"Updated package: {package_name} v{package_version}")
        return jsonify(response_dict), 200

    except Exception as e:
        logger.error(f"Error updating package {package_id}: {str(e)}")
        return jsonify({"error": str(e)}), 400


@bp.route("/<int:package_id>", methods=["DELETE"])
def delete_package(package_id: int):
    """Delete a package by ID."""
    try:
        with get_db_session() as session:
            db_package = session.get(Package, package_id)
            if not db_package:
                return jsonify({"error": "Package not found"}), 404

            package_name = db_package.name
            package_version = db_package.version

            session.delete(db_package)

        logger.info(f"Deleted package: {package_name} v{package_version}")
        return jsonify({"message": "Package deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting package {package_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500
