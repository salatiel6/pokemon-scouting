from typing import Any, Tuple

from flask import Flask, jsonify
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.db import db
from app.handlers.logger import logger
from app.handlers.pokeapi_client import PokeAPIError, PokemonNotFoundError


def handle_validation_error(err: ValidationError) -> Tuple[Any, int]:
    """
    Handle Pydantic validation errors and return a 400 JSON response.

    :param err: an instance of pydantic.ValidationError

    :return: A tuple (JSON response, HTTP 400)
    """
    return (
        jsonify(
            {
                "error": "validation_error",
                "details": err.errors(),
            }
        ),
        400,
    )


def handle_pokemon_not_found(err: PokemonNotFoundError) -> Tuple[Any, int]:
    """
    Handle domain not-found errors for Pokemon lookups and return 404.

    :param err: a PokemonNotFoundError instance

    :return: A tuple (JSON response, HTTP 404)
    """
    return (
        jsonify(
            {
                "error": "pokemon_not_found",
                "message": str(err),
            }
        ),
        404,
    )


def handle_upstream_error(err: PokeAPIError) -> Tuple[Any, int]:
    """
    Handle upstream PokeAPI errors and return a 502 JSON response.

    :param err: a PokeAPIError instance

    :return: A tuple (JSON response, HTTP 502)
    """
    return (
        jsonify(
            {
                "error": "upstream_error",
                "message": str(err),
            }
        ),
        502,
    )


def handle_db_error(err: SQLAlchemyError) -> Tuple[Any, int]:
    """
    Handle database errors, perform a session rollback, and return 500.

    :param err: a SQLAlchemyError instance

    :return: A tuple (JSON response, HTTP 500)
    """
    try:
        db.session.rollback()
    except Exception as e:
        logger.error(f"rollback error: {e}")
        pass
    return (
        jsonify(
            {
                "error": "database_error",
                "message": str(err),
            }
        ),
        500,
    )


def handle_unexpected_error(_err: Exception) -> Tuple[Any, int]:
    """
    Catch-all handler for unexpected exceptions, returning a 500 JSON response.

    :param _err: any unexpected exception

    :return: A tuple (JSON response, HTTP 500)
    """
    return (
        jsonify(
            {
                "error": "internal_server_error",
                "message": "An unexpected error occurred.",
            }
        ),
        500,
    )


def register_error_handlers(app: Flask) -> None:
    """
    Register global JSON error handlers on the provided Flask app instance.

    This function wires top-level handler functions without nesting them,
    keeping registration separate from the handler implementations.

    :param app: a Flask application instance

    :return: None
    """
    app.register_error_handler(ValidationError, handle_validation_error)
    app.register_error_handler(PokemonNotFoundError, handle_pokemon_not_found)
    app.register_error_handler(PokeAPIError, handle_upstream_error)
    app.register_error_handler(SQLAlchemyError, handle_db_error)
    app.register_error_handler(Exception, handle_unexpected_error)
