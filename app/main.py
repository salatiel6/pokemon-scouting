from flask import Flask

from app.api.routes import register_routes
from app.db import init_db
from app.handlers.errors import register_error_handlers
from app.handlers.middlewares import register_middlewares


def create_app() -> Flask:
    """
    Create and configure the Flask application instance.

    :return: A configured Flask app_ instance
    :raises: None
    """
    app_ = Flask(__name__)

    # Basic configuration with sensible defaults for a simple case study
    app_.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///pokemon.db")
    app_.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app_.config.setdefault("POKEAPI_BASE_URL", "https://pokeapi.co/api/v2")

    # Initialize database, middlewares, and register HTTP routes
    init_db(app_)
    register_middlewares(app_)
    register_routes(app_)
    register_error_handlers(app_)

    return app_


app = create_app()


if __name__ == "__main__":
    # Run the development server
    app.run(host="0.0.0.0", port=5000, debug=True)
