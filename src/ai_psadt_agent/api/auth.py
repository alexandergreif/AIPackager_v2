"""Authentication and rate limiting middleware for API endpoints."""

import os
from functools import wraps
from typing import Callable, Optional, Tuple, TypeVar, Union  # Added Union, Tuple, Any

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request  # Added Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from loguru import logger
from typing_extensions import ParamSpec  # For older Pythons, but 3.11 has it in typing

# Load environment variables
load_dotenv()

# For precise decorator typing (Python 3.10+)
P = ParamSpec("P")
R = TypeVar("R")


def get_api_key() -> Optional[str]:
    """Get API key from environment variables.

    Returns:
        API key if configured, None otherwise
    """
    return os.getenv("API_KEY")


def require_api_key(f: Callable[P, R]) -> Callable[P, Union[R, Tuple[Response, int]]]:
    """Decorator to require API key authentication.

    Args:
        f: Function to wrap

    Returns:
        Wrapped function
    """

    @wraps(f)
    def decorated_function(*args: P.args, **kwargs: P.kwargs) -> Union[R, Tuple[Response, int]]:
        # Get configured API key
        configured_api_key = get_api_key()

        # If no API key is configured, allow access (for development)
        if not configured_api_key:
            logger.warning("No API key configured - allowing access")
            return f(*args, **kwargs)

        # Check for API key in headers
        provided_api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")

        # Handle Bearer token format
        if provided_api_key and provided_api_key.startswith("Bearer "):
            provided_api_key = provided_api_key[7:]  # Remove 'Bearer ' prefix

        if not provided_api_key:
            logger.warning(f"API key missing for {request.endpoint}")
            return jsonify(
                {
                    "error": "API key required",
                    "message": "Please provide API key in X-API-Key header or Authorization header",
                }
            ), 401

        if provided_api_key != configured_api_key:
            logger.warning(f"Invalid API key provided for {request.endpoint}")
            return jsonify(
                {
                    "error": "Invalid API key",
                    "message": "The provided API key is not valid",
                }
            ), 401

        logger.debug(f"API key validated for {request.endpoint}")
        return f(*args, **kwargs)

    return decorated_function


def init_limiter(app: Flask) -> Limiter:
    """Initialize Flask-Limiter for rate limiting.

    Args:
        app: Flask application instance

    Returns:
        Limiter instance
    """
    # Configure rate limiting storage
    storage_uri = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")

    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=storage_uri,
        default_limits=["1000 per day", "100 per hour"],
        headers_enabled=True,
    )

    logger.info("Rate limiting initialized")
    return limiter


def apply_generation_rate_limit() -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Apply rate limit for generation endpoints (100 req / 10 min per .clinerules).

    This is a decorator factory that returns the actual decorator.
    """

    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @wraps(f)
        def decorated_function_inner(*args: P.args, **kwargs: P.kwargs) -> R:
            # Rate limiting is handled by Flask-Limiter decorators on routes
            return f(*args, **kwargs)

        return decorated_function_inner

    return decorator


# Rate limit configurations
GENERATION_RATE_LIMIT = "100 per 10 minutes"
VALIDATION_RATE_LIMIT = "200 per 10 minutes"
SEARCH_RATE_LIMIT = "500 per 10 minutes"
