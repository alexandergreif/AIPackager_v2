from typing import Any

from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.route("/healthz", methods=["GET"])
def healthz() -> Any:
    return jsonify({"status": "ok"})
