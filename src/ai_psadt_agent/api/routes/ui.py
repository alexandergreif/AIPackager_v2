import time
from typing import Generator, Union

from flask import Blueprint, Response, render_template, request, url_for

ui_bp = Blueprint("ui_bp", __name__, template_folder="../../templates/ui")


@ui_bp.route("/upload", methods=["GET"])
def upload_page() -> str:
    """Renders the upload page."""
    return render_template("upload.html")


@ui_bp.route("/packages", methods=["POST"])
def create_package_from_form() -> Union[Response, tuple[str, int]]:
    """Handles the HTMX form submission for creating a new package."""
    # This will be the target for the HTMX form
    # It will handle the file upload and then call the service layer
    # to create the package, similar to the existing API endpoint.

    if "package_file" not in request.files:
        return "No file part", 400

    file = request.files["package_file"]
    # prompt = request.form.get("prompt_text", "") # Will be used later

    if not file or not file.filename:
        return "No selected file", 400

    # In a real app, you'd save this to a secure location
    # and pass the path to the service layer.
    # For now, we'll just confirm we received it.
    # filename = secure_filename(file.filename)

    # For SP5-01, the goal is to accept the post and redirect.
    # The actual package creation logic will be fleshed out.
    # We'll simulate a successful creation and get a package_id.

    # Placeholder for package creation logic
    # package = package_service.create(file, prompt)
    # package_id = package.id

    # For now, let's use a dummy ID for the redirect.
    package_id = "dummy-uuid-12345"

    # Redirect to the progress page, as per SP5-02
    response = Response(status=201)
    response.headers["HX-Redirect"] = url_for("ui_bp.progress_page", package_id=package_id)
    return response


@ui_bp.route("/progress/<string:package_id>")
def progress_page(package_id: str) -> str:
    """Renders the progress page for a given package ID."""
    return render_template("progress.html", package_id=package_id)


@ui_bp.route("/v1/progress/<string:package_id>")
def sse_progress(package_id: str) -> Response:
    """Streams progress updates using Server-Sent Events."""

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
