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


@ui_bp.route("/history")
def history_page() -> str:
    """Renders the package history page with pagination."""
    # In a real implementation, you would fetch this from the database.
    # We'll mock this for now.
    from datetime import datetime

    class MockPagination:
        def __init__(self, page: int, per_page: int, total: int) -> None:
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1

    class MockPackage:
        def __init__(
            self,
            id: int,
            name: str,
            version: str,
            installer_path: str,
            created_at: datetime,
            updated_at: datetime,
        ) -> None:
            self.id = id
            self.name = name
            self.version = version
            self.installer_path = installer_path
            self.created_at = created_at
            self.updated_at = updated_at

    page = request.args.get("page", 1, type=int)
    per_page = 10

    # Mock data
    all_packages = [
        MockPackage(i, f"Package {i}", f"1.{i}.0", f"/path/to/installer_{i}.msi", datetime.now(), datetime.now())
        for i in range(1, 26)
    ]
    all_packages.reverse()  # Newest first

    total = len(all_packages)
    packages_on_page = all_packages[(page - 1) * per_page : page * per_page]

    pagination = MockPagination(page, per_page, total)

    return render_template("history.html", packages=packages_on_page, pagination=pagination)


@ui_bp.route("/packages/<int:package_id>/download")
def download_package_script(package_id: int) -> Response:
    """Downloads the generated script for a given package."""
    # In a real implementation, fetch the script text from the database.
    # We'll mock this for now.
    script_text = f"Write-Host 'This is the script for package {package_id}'"

    return Response(
        script_text,
        mimetype="text/plain",
        headers={"Content-disposition": f"attachment; filename=Deploy-Application-Package-{package_id}.ps1"},
    )
