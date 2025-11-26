# ruff: noqa: E402

import os

# Ensure required environment variables for Settings
os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///test-default.db")
os.environ.setdefault("POKEAPI_BASE_URL", "https://pokeapi.co/api/v2")
os.environ.setdefault("SYNC_ON_START", "false")
os.environ.setdefault("CACHE_TYPE", "NullCache")
os.environ.setdefault("CACHE_DEFAULT_TIMEOUT", "120")
os.environ.setdefault("STALE_TTL_MINUTES", "30")
os.environ.setdefault("DISABLE_BACKGROUND_SYNC", "true")
os.environ.setdefault("SYNC_INTERVAL_MINUTES", "30")
os.environ.setdefault("REFRESH_BATCH_SIZE", "10")

from typing import Any, Generator

import pytest
from flask import Flask

from app.api.health import health_bp
from app.api.pokemon import pokemon_bp
from app.db import db, init_db
from app.handlers.errors import register_error_handlers
from app.handlers.middlewares import register_middlewares


@pytest.fixture()
def app(tmp_path) -> Generator[Flask, Any, None]:
    """
    Create a Flask app instance configured for testing with an isolated SQLite DB.

    :param tmp_path: pytest-provided temporary directory path fixture

    :return: A configured Flask application instance for tests
    :raises: None
    """
    flask_app = Flask(__name__)
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///test-default.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        POKEAPI_BASE_URL="https://pokeapi.co/api/v2",
    )

    # Wire up app like our factory does
    init_db(flask_app)
    register_middlewares(flask_app)
    # Register API blueprints
    flask_app.register_blueprint(pokemon_bp)
    flask_app.register_blueprint(health_bp)
    register_error_handlers(flask_app)

    yield flask_app


@pytest.fixture()
def client(app: Flask):
    """
    Provide a Flask test client bound to the application context.

    :param app: The Flask test application

    :return: A FlaskClient for issuing HTTP requests in tests
    :raises: None
    """
    with app.app_context():
        yield app.test_client()


@pytest.fixture(autouse=True)
def _clean_db(app: Flask) -> Generator[None, None, None]:
    """
    Ensure a clean database state per test by truncating all tables.

    :param app: The Flask application

    :return: None
    :raises: None
    """
    # Before test: nothing to do (DB was just created)
    yield
    # After test: drop all and recreate for isolation
    with app.app_context():
        db.drop_all()
        db.create_all()
