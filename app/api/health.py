from flask import Blueprint

health_bp = Blueprint("health", __name__)


def health() -> tuple[dict, int]:
    """
    Simple health check endpoint.

    :return: JSON with status ok and HTTP 200
    :raises: None
    """
    return {"status": "ok"}, 200


def register_health_routes() -> None:
    """
    Register health routes on the health blueprint.

    :return: None
    :raises: None
    """
    health_bp.add_url_rule("/health", view_func=health, methods=["GET"])


# Register routes when module is imported
register_health_routes()
