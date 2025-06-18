import json
import os
import sys
from typing import Any, Dict  # Removed Callable

from flask import Flask
from flask_cors import CORS
from loguru import logger
from prometheus_flask_exporter import PrometheusMetrics


def create_app() -> Flask:
    """Application factory pattern for Flask app."""
    app = Flask(__name__)

    # Configure CORS
    CORS(app)

    # Initialize Prometheus metrics
    metrics = PrometheusMetrics(app)

    # Add custom info metric
    metrics.info("app_info", "Application info", version="1.0.0")

    # Custom metrics for AI generation
    generation_counter = metrics.counter(
        "psadt_script_generations_total",
        "Total number of PSADT script generations",
        labels={"status": lambda: "unknown"},
    )

    generation_duration = metrics.histogram(
        "psadt_script_generation_duration_seconds",
        "Time spent generating PSADT scripts",
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    )

    # Database metrics
    db_operations = metrics.counter(
        "psadt_database_operations_total",
        "Total database operations",
        labels={"operation": lambda: "unknown", "status": lambda: "unknown"},
    )

    # Store metrics for access in routes
    app.config["METRICS"] = {
        "generation_counter": generation_counter,
        "generation_duration": generation_duration,
        "db_operations": db_operations,
    }

    # Configure Loguru logging
    logger.remove()  # Remove default handler

    # Get log format from environment
    log_format = os.getenv("LOG_FORMAT", "human").lower()

    if log_format == "structured":
        # Structured JSON logging
        def json_formatter(record: Dict[str, Any]) -> str:  # Added type hints
            log_entry = {
                "timestamp": record["time"].isoformat(),
                "level": record["level"].name,
                "logger": record["name"],
                "function": record["function"],
                "line": record["line"],
                "message": record["message"],
                "module": record["module"],
                "process": record["process"].id,
                "thread": record["thread"].id,
            }

            # Add extra fields if present
            if record.get("extra"):
                log_entry.update(record["extra"])

            return json.dumps(log_entry)

        logger.add(
            sys.stdout,
            format=json_formatter,
            level="INFO",
            serialize=False,
        )
    else:
        # Human-readable logging (default)
        log_format_str = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        logger.add(
            sys.stdout,
            format=log_format_str,
            level="INFO",
        )

    # Initialize rate limiting
    from .api.auth import init_limiter

    init_limiter(app)

    # Register blueprints
    from .api.routes.generation import bp as generation_bp
    from .api.routes.health import bp as health_bp
    from .api.routes.packages import bp as packages_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(packages_bp)
    app.register_blueprint(generation_bp)

    # Add OpenAPI docs endpoint
    @app.route("/docs")
    def docs() -> Dict[str, Any]:  # Added type hint
        """Serve OpenAPI documentation."""
        return {"info": {"title": "PSADT AI Agent API", "version": "1.0.0"}}

    logger.info("Flask application initialized successfully")
    return app
