import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app: Flask) -> None:
    """
    Initialize the SQLAlchemy extension and create all tables if needed.

    :param app: A Flask application instance

    :return: None
    """
    db.init_app(app)
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "sqlite:///pokemon.db")
    if uri.startswith("sqlite"):
        path = uri.replace("sqlite:///", "")
        folder = os.path.dirname(path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

    with app.app_context():
        # This local import avoids circular import issues at module import time
        from app.models import pokemon as _models  # noqa: F401

        db.create_all()
