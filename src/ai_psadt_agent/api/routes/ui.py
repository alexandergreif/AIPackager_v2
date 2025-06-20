import time
import uuid
from math import ceil
from typing import Generator, Union

from flask import Blueprint, current_app, redirect, render_template, request, url_for
from loguru import logger
from werkzeug.wrappers import Response

from ...domain_models.package import Package, StatusEnum
from ...infrastructure.db.session import get_db_session
from ...services.file_utils import get_upload_path
from ...services.generation_service import run_generation_in_background

ui_bp = Blueprint("ui_bp", __name__, template_folder="../../templates/ui")


@ui_bp.route("/")
def index() -> Response:
    """Redirects to the upload page."""
    return redirect(url_for("ui_bp.upload_page"))


@ui_bp.route("/upload", methods=["GET"])
def upload_page() -> str:
    """Renders the upload page."""
    return render_template("upload.html")


@ui_bp.route("/packages", methods=["POST"])
def create_package_from_form() -> Union[Response, tuple[str, int]]:
    """Handles the HTMX form submission for creating a new package."""
    if "package_file" not in request.files:
        return "No file part", 400

    file = request.files["package_file"]
    prompt = request.form.get("prompt_text", "")

    if not file or not file.filename:
        return "No selected file", 400

    # Generate UUID for the package
    package_uuid = uuid.uuid4()

    # Generate secure upload path
    upload_path = get_upload_path(str(package_uuid), file.filename)

    try:
        # Ensure the upload directory exists
        upload_path.parent.mkdir(parents=True, exist_ok=True)

        # Save the uploaded file to disk
        file.save(upload_path)
        logger.info(f"Saved uploaded file to {upload_path}")

    except (OSError, IOError) as e:
        logger.error(f"Failed to save uploaded file: {e}")
        return f"Failed to save file: {str(e)}", 500

    # Create the package record with actual file path
    with get_db_session() as session:
        new_package = Package(
            package_id=package_uuid,
            name=file.filename,
            version="1.0",  # Placeholder
            installer_path=str(upload_path),
            status=StatusEnum.PENDING,
            stage="Queued",
            script_text=prompt,  # Using the prompt
        )
        session.add(new_package)
        session.commit()
        session.refresh(new_package)
        package_id = new_package.package_id

    # Trigger the background generation job
    app = current_app._get_current_object()
    run_generation_in_background(str(package_id), app)

    response = Response(status=201)
    response.headers["HX-Redirect"] = url_for("ui_bp.progress_page", package_id=str(package_id))
    return response


@ui_bp.route("/progress/<string:package_id>")
def progress_page(package_id: str) -> str:
    """Renders the progress page for a given package ID."""
    return render_template("progress.html", package_id=package_id)


@ui_bp.route("/v1/progress/<string:package_id>")
def sse_progress(package_id: str) -> Response:
    """Streams progress updates using Server-Sent Events."""

    def generate() -> Generator[str, None, None]:
        with logger.contextualize(package_id=package_id):
            logger.info("Starting SSE progress stream for real.")
            last_progress = -1
            last_message = ""
            package_uuid = uuid.UUID(package_id)

            while True:
                with get_db_session() as session:
                    package = session.query(Package).filter(Package.package_id == package_uuid).first()

                    if not package:
                        logger.warning("Package not found, stopping SSE stream.")
                        break

                    if package.progress != last_progress:
                        bar_html = (
                            f'<div id="progress-bar" class="bg-indigo-600 h-6 rounded-full text-center text-white" '
                            f'style="width: {package.progress}%">{package.progress}%</div>'
                        )
                        yield f"event: progressbar\ndata: {bar_html}\n\n"
                        last_progress = package.progress

                    if package.status_message and package.status_message != last_message:
                        message_html = f'<div id="progress-message" class="text-center">{package.status_message}</div>'
                        yield f"event: message\ndata: {message_html}\n\n"
                        last_message = package.status_message

                    if package.status in [StatusEnum.COMPLETED, StatusEnum.FAILED]:
                        logger.info(f"Package generation finished with status: {package.status.value}")
                        redirect_url = url_for("ui_bp.history_page")
                        yield f'event: done\ndata: {{"redirect_url": "{redirect_url}"}}\n\n'
                        break
                time.sleep(1)

    return Response(generate(), mimetype="text/event-stream")


class Pagination:
    def __init__(self, page: int, per_page: int, total: int) -> None:
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = ceil(total / per_page)
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1
        self.next_num = page + 1


@ui_bp.route("/history")
def history_page() -> str:
    """Renders the package history page with pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = 10
    with get_db_session() as session:
        total = session.query(Package).count()
        packages = (
            session.query(Package)
            .order_by(Package.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
    pagination = Pagination(page, per_page, total)
    return render_template("history.html", packages=packages, pagination=pagination)


@ui_bp.route("/packages/<int:package_id>/download")
def download_package_script(package_id: int) -> Response:
    """Downloads the generated script for a given package."""
    with get_db_session() as session:
        package = session.get(Package, package_id)
        if not package or not package.script_text:
            return Response("Script not found.", status=404)

        script_text = package.script_text

    return Response(
        script_text,
        mimetype="text/plain",
        headers={
            "Content-disposition": f"attachment; filename=Deploy-Application-{package.name}-{package.version}.ps1"
        },
    )
