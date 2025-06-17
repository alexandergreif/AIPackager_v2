from flask import Flask
from flask_cors import CORS
from loguru import logger
import sys


def create_app() -> Flask:
    """Application factory pattern for Flask app."""
    app = Flask(__name__)

    # Configure CORS
    CORS(app)

    # Configure Loguru logging
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )

    # Register blueprints
    from .api.routes.health import bp as health_bp
    from .api.routes.packages import bp as packages_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(packages_bp)

    # Add OpenAPI docs endpoint
    @app.route("/docs")
    def docs():
        """Serve OpenAPI documentation."""
        return {"info": {"title": "PSADT AI Agent API", "version": "1.0.0"}}

    logger.info("Flask application initialized successfully")
    return app
