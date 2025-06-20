import threading
import uuid
from pathlib import Path
from typing import Any

from loguru import logger

from ..domain_models.package import Package, StatusEnum
from ..infrastructure.db.session import get_db_session
from ..metadata.extract import extract_metadata
from .prompt_templates import InstallerMetadata
from .script_generator import ScriptGenerator


def run_generation_in_background(package_id: str, app_context: Any) -> None:
    """Runs the script generation in a background thread."""
    thread = threading.Thread(target=generate_and_update_package, args=(package_id, app_context))
    thread.daemon = True
    thread.start()


def generate_and_update_package(package_id: str, app: Any) -> None:
    """The target function for the background thread."""
    with app.app_context():
        logger.info(f"Starting background generation for package_id: {package_id}")
        with get_db_session() as session:
            package = session.query(Package).filter(Package.package_id == uuid.UUID(package_id)).first()
            if not package:
                logger.error(f"Package with id {package_id} not found.")
                return

            package.status = StatusEnum.IN_PROGRESS
            session.commit()

            def progress_callback(progress: int, message: str) -> None:
                """Callback to update package progress in the database."""
                with get_db_session() as inner_session:
                    pkg_to_update = (
                        inner_session.query(Package).filter(Package.package_id == uuid.UUID(package_id)).first()
                    )
                    if pkg_to_update:
                        pkg_to_update.progress = progress
                        pkg_to_update.status_message = message
                        inner_session.commit()
                logger.debug(f"Progress for {package_id}: {progress}% - {message}")

            try:
                script_generator = ScriptGenerator()

                # Extract real metadata from the uploaded installer file
                progress_callback(10, "Extracting metadata from installer file...")

                if package.installer_path:
                    installer_path = Path(package.installer_path)
                    installer_metadata = extract_metadata(installer_path)
                    logger.info(f"Extracted metadata: {installer_metadata.name} v{installer_metadata.version}")
                else:
                    # Fallback to package data if no installer path
                    installer_metadata = InstallerMetadata(
                        name=package.name,
                        version=package.version or "1.0.0",
                        vendor="Unknown",
                        installer_type="exe",
                        silent_args="/S",
                        architecture="x64",
                        language="EN",
                    )
                    logger.warning(f"No installer path found for package {package_id}, using fallback metadata")

                progress_callback(30, "Generating PSADT script...")

                # Generate script with extracted metadata
                result = script_generator.generate_script(
                    installer_metadata=installer_metadata,
                    user_notes=package.script_text,
                )

                if result and result.structured_script:
                    package.script_text = result.script_content
                    package.status = StatusEnum.COMPLETED
                    package.progress = 100
                    package.status_message = "Completed"
                    logger.success(f"Successfully generated script for package {package_id}")
                else:
                    raise Exception("Script generation failed to produce a result.")

            except Exception as e:
                logger.error(f"Error during script generation for {package_id}: {e}")
                package.status = StatusEnum.FAILED
                package.status_message = f"Failed: {str(e)}"

            finally:
                session.add(package)
                session.commit()
