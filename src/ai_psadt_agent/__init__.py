import os
import sys
from pathlib import Path

# Removed unused: json, typing.Any, typing.Dict
from flask import Flask
from flask_cors import CORS
from loguru import logger
from prometheus_client import REGISTRY  # Import REGISTRY
from prometheus_flask_exporter import PrometheusMetrics


def _unregister_metrics(metric_names: list[str]) -> None:  # Added return type
    """Helper to unregister specific Prometheus metrics."""
    for collector_obj in list(REGISTRY._collector_to_names.keys()):
        collector_metric_names = REGISTRY._collector_to_names[collector_obj]
        should_unregister = False
        for base_name_to_check in metric_names:
            if any(base_name_to_check in c_name for c_name in collector_metric_names):
                should_unregister = True
                break
        if should_unregister:
            try:
                REGISTRY.unregister(collector_obj)
                logger.debug(f"Unregistered existing Prometheus metric collector: {collector_obj}")
            except Exception as e:  # pylint: disable=broad-except
                logger.warning(f"Could not unregister metric collector {collector_obj}: {e}")


def resume_incomplete_jobs() -> None:
    """Find and resume jobs that were in progress when the app last shut down."""
    # This is a placeholder for the actual job resumption logic.
    # In a real application, you would query the database for packages
    # with status 'IN_PROGRESS' and restart their generation process,
    # likely using a background worker queue (e.g., Celery, RQ).
    logger.info("Checking for incomplete jobs to resume...")
    # from .domain_models.package import Package, StatusEnum
    # from .infrastructure.db.session import get_session
    # with get_session() as session:
    #     in_progress_packages = session.query(Package).filter(Package.status == StatusEnum.IN_PROGRESS).all()
    #     for package in in_progress_packages:
    #         logger.info(f"Resuming job for package {package.package_id}")
    #         # enqueue_generation_task(package.id)
    pass


def create_app() -> Flask:
    """Application factory pattern for Flask app."""
    app = Flask(__name__)
    CORS(app)
    metrics = PrometheusMetrics(app)

    metrics_to_clear_on_startup = [
        "app_info",
        "psadt_script_generations_total",
        "psadt_script_generation_duration_seconds",
        "psadt_database_operations_total",
    ]
    _unregister_metrics(metrics_to_clear_on_startup)

    # Import prometheus_client metrics types
    from prometheus_client import Counter, Histogram

    # Define metrics using prometheus_client directly
    # These will be registered with the default REGISTRY,
    # which prometheus-flask-exporter serves by default.

    # Ensure app_info is also using prometheus_client directly if it's part of the same pattern,
    # or keep it with metrics.info if that's fine.
    # For consistency, let's assume all custom metrics follow the new pattern.
    # However, metrics.info is specific to prometheus-flask-exporter for app info. So keep it.
    metrics.info("app_info", "Application info", version="1.0.0")

    generation_counter = Counter(
        "psadt_script_generations_total",
        "Total number of PSADT script generations",
        labelnames=["status"],  # Use labelnames for prometheus_client
    )

    generation_duration = Histogram(
        "psadt_script_generation_duration_seconds",
        "Time spent generating PSADT scripts",
        labelnames=["endpoint"],  # Use labelnames for prometheus_client
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    )

    db_operations = Counter(
        "psadt_database_operations_total",
        "Total database operations",
        labelnames=["operation", "status"],  # Use labelnames for prometheus_client
    )

    app.config["METRICS"] = {
        "generation_counter": generation_counter,
        "generation_duration": generation_duration,
        "db_operations": db_operations,
    }

    logger.remove()
    log_format = os.getenv("LOG_FORMAT", "human").lower()

    # Ensure logs directory exists
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file_path = logs_dir / "api.json"

    if log_format == "structured":
        logger.add(log_file_path, level="INFO", serialize=True, rotation="10 MB", compression="zip")
    else:
        # Also log to console in human-readable format for development
        log_format_str = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        logger.add(sys.stdout, format=log_format_str, level="INFO")
        # And still log to JSON file
        logger.add(log_file_path, level="INFO", serialize=True, rotation="10 MB", compression="zip")

    from .api.auth import init_limiter

    init_limiter(app)

    from .api.routes.generation import bp as generation_bp
    from .api.routes.health import bp as health_bp
    from .api.routes.packages import bp as packages_bp
    from .api.routes.ui import ui_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(packages_bp)
    app.register_blueprint(generation_bp)
    app.register_blueprint(ui_bp)

    from .api import init_api_docs

    init_api_docs(app)

    with app.app_context():
        resume_incomplete_jobs()

    logger.info("Flask application initialized successfully")
    return app
