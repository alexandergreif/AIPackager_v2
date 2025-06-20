import time
from math import ceil
from typing import Generator, Union

from flask import Blueprint, Response, render_template, request, url_for
from loguru import logger

from ...domain_models.package import Package, StatusEnum
from ...infrastructure.db.session import get_db_session

ui_bp = Blueprint("ui_bp", __name__, template_folder="../../templates/ui")


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

    # This would be handled by a proper service layer
    with get_db_session() as session:
        new_package = Package(
            name=file.filename,
            version="1.0",  # Placeholder
            installer_path=f"/uploads/{file.filename}",  # Placeholder
            status=StatusEnum.PENDING,
            stage="Queued",
            script_text=prompt,  # Using the prompt
        )
        session.add(new_package)
        session.commit()
        session.refresh(new_package)
        package_id = new_package.package_id

    # In a real app, you would now trigger the background job
    # For now, the SSE endpoint will just simulate the progress.

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
    with logger.contextualize(package_id=package_id):
        logger.info("Starting SSE progress stream.")

    def generate() -> Generator[str, None, None]:
        # Simulate a multi-step generation process
        stages = {
            10: "Analyzing installer...",
            30: "Querying knowledge base...",
            50: "Generating script logic...",
            70: "Rendering PowerShell script...",
            90: "Finalizing package...",
            100: "Complete!",
        }

        for percentage, message in stages.items():
            # This is where you would get the actual progress from your background job
            time.sleep(1.5)  # Simulate work being done

            # The message format for SSE is specific.
            # We send an "event" name and "data".
            # HTMX can use the event name to swap specific elements.

            # Update the progress bar
            bar_html = (
                f'<div id="progress-bar" class="bg-indigo-600 h-6 rounded-full text-center text-white" '
                f'style="width: {percentage}%">{percentage}%</div>'
            )
            yield f"event: progressbar\ndata: {bar_html}\n\n"

            # Update the status message
            message_html = f'<div id="progress-message" class="text-center">{message}</div>'
            yield f"event: message\ndata: {message_html}\n\n"

        # Send a final event to indicate completion, maybe for a redirect
        time.sleep(1)
        yield 'event: done\ndata: {"redirect_url": "/history"}\n\n'

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
