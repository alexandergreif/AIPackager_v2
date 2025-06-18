"""API package for Flask blueprints and OpenAPI documentation."""

from flask import Flask

# from flask_pydantic import FlaskPydantic  # Mypy: "flask_pydantic" has no attribute "FlaskPydantic"

# Example Pydantic models for documentation (if not defined elsewhere)
# These would typically be your request/response models from routes.
# For now, let's assume they might be defined in individual route files
# or a common domain_models location.


# Initialize FlaskPydantic
# The actual configuration (title, version, etc.) can be done here
# or when calling init_app.
# api_docs = FlaskPydantic(
#     title="PSADT AI Agent API",
#     version="1.0.0",
#     description="API for generating PowerShell App Deployment Toolkit (PSADT) scripts using AI.",
#     path="/docs",  # Default path for OpenAPI UI
#     openapi_path="/openapi.json",  # Default path for schema
# )


def init_api_docs(app: Flask) -> None:
    """Initialize Flask-Pydantic with the Flask app.

    This function should be called from the application factory (create_app).
    It registers the OpenAPI documentation endpoints.
    """
    # api_docs.init_app(app) #TODO: Fix FlaskPydantic import and usage
    pass  # Placeholder to avoid empty function body if all lines are commented
    # You can also register Pydantic models for specific blueprints here if needed,
    # though often models are associated directly with route decorators.
    # Example:
    # from .routes.packages import PackageResponse, CreatePackageRequest
    # api_docs.register_blueprint_model(packages_bp, PackageResponse)
    # api_docs.register_blueprint_model(packages_bp, CreatePackageRequest)
