from typing import Any

from flask import Flask, jsonify, request

from app.db import db
from app.db.config import read_pokemon_csv
from app.handlers.ingest_service import IngestService
from app.handlers.logger import logger
from app.models.pokemon import Pokemon
from app.schemas.pokemon import (
    IngestResult,
    PokemonDetail,
    PokemonIngestRequest,
    TypesFilterRequest,
)


def _to_detail_dict(pokemon: Pokemon) -> dict:
    """
    Convert a Pokemon ORM instance to a full detail dictionary using the
    PokemonDetail schema to ensure a consistent shape.

    :param pokemon: a Pokemon ORM instance

    :return: A dict with full Pokemon details
    """
    detail = PokemonDetail.model_validate(pokemon)
    return detail.model_dump()


def ingest() -> tuple[Any, int]:
    """
    Trigger ingestion for a list of Pokemon names.

    :return: A JSON response with the ingestion result and status 202
    """
    logger.info("Ingesting Pokemon...")

    payload = request.get_json(silent=True) or {}
    data = PokemonIngestRequest(**payload)
    names: list[str] = data.names

    if not names:
        names = read_pokemon_csv()

    service = IngestService()
    result_dict = service.ingest_many(names)
    result = IngestResult(**result_dict)

    return jsonify(result.model_dump()), 202


def add_pokemon() -> tuple[Any, int]:
    """
    Add or update Pokemon by providing names in the request body.

    :return: A JSON response with the ingestion result and status 202
    """
    logger.info("Adding Pokemon...")

    payload = request.get_json(silent=True) or {}
    data = PokemonIngestRequest(**payload)

    service = IngestService()

    result_dict = service.ingest_many(data.names)
    result = IngestResult(**result_dict)

    return jsonify(result.model_dump()), 202


def list_pokemon() -> Any:
    """
    list Pokemon resources with optional name filter and limit.

    :return: A JSON array of full PokemonDetail objects
    """
    logger.info("Listing Pokemon...")

    q = Pokemon.query
    name_filter = request.args.get("name")
    if name_filter:
        q = q.filter(Pokemon.name.ilike(f"%{name_filter}%"))

    limit = request.args.get("limit", default=200, type=int)
    if not isinstance(limit, int) or limit <= 0:
        limit = 200

    items = [_to_detail_dict(p) for p in q.limit(limit).all()]

    return jsonify(items)


def get_pokemon_by_id(pokemon_id: str) -> tuple[Any, int] | Any:
    """
    Retrieve a single Pokemon by internal ID (UUID v4 string).

    :param pokemon_id: Pokemon UUID identifier

    :return: PokemonDetail JSON or 404
    """
    logger.info("Retrieving Pokemon by ID...")

    p = Pokemon.query.filter_by(id=pokemon_id).first()
    if not p:
        return jsonify({"error": "not_found"}), 404

    return jsonify(_to_detail_dict(p))


def get_pokemon_by_name(name: str) -> tuple[Any, int] | Any:
    """
    Retrieve a single Pokemon by canonical name.

    :param name: Pokemon canonical name

    :return: PokemonDetail JSON or 404
    """
    logger.info("Retrieving Pokemon by name...")

    p = Pokemon.query.filter_by(name=name.lower()).first()
    if not p:
        return jsonify({"error": "not_found"}), 404

    return jsonify(_to_detail_dict(p))


def get_pokemon_by_pokedex(pokedex_number: int) -> tuple[Any, int] | Any:
    """
    Retrieve a single Pokemon by National Pokedex number.

    :param pokedex_number: integer Pokedex number

    :return: PokemonDetail JSON or 404
    """
    logger.info("Retrieving Pokemon by Pokédex number...")

    p = Pokemon.query.filter_by(pokedex_number=int(pokedex_number)).first()
    if not p:
        return jsonify({"error": "not_found"}), 404

    return jsonify(_to_detail_dict(p))


def list_pokemon_by_type() -> Any:
    """
    List Pokemon that match ANY of the provided types.

    :return: A JSON array of full PokemonDetail objects matching any type
    """
    logger.info("Listing Pokemon by types...")

    payload = request.get_json(silent=True) or {}
    req = TypesFilterRequest(**payload)
    if not req.types:
        return jsonify([])

    limit = request.args.get("limit", default=200, type=int)
    if not isinstance(limit, int) or limit <= 0:
        limit = 200

    wanted = set(req.types)
    matches: list[Pokemon] = []

    for p in Pokemon.query.all():
        p_types = set(p.types or [])
        if p_types.intersection(wanted):
            matches.append(p)
            if len(matches) >= limit:
                break
    items = [_to_detail_dict(p) for p in matches]

    return jsonify(items)


def delete_pokemon(pokemon_id: str) -> tuple[Any, int]:
    """
    Delete a Pokemon by internal ID (UUID).

    :param pokemon_id: path parameter with id

    :return: Empty response with 204 on success, or 404 if not found
    """
    logger.info("Deleting Pokemon...")

    p = Pokemon.query.filter_by(id=pokemon_id).first()

    if not p:
        return jsonify({"error": "not_found"}), 404

    db.session.delete(p)
    db.session.commit()
    return "", 204


def register_routes(app: Flask) -> None:
    """
    Register all HTTP endpoints on the provided Flask app instance.

    This function adds URL rules mapping paths to top-level view functions,
    keeping handlers separated from registration logic.

    :param app: a Flask application instance

    :return: None
    """
    app.add_url_rule("/ingest", view_func=ingest, methods=["POST"])
    app.add_url_rule("/add-pokemon", view_func=add_pokemon, methods=["POST"])
    app.add_url_rule("/pokemon", view_func=list_pokemon, methods=["GET"])
    app.add_url_rule("/pokemon/id/<pokemon_id>", view_func=get_pokemon_by_id, methods=["GET"])
    app.add_url_rule("/pokemon/name/<name>", view_func=get_pokemon_by_name, methods=["GET"])
    app.add_url_rule("/pokemon/pokedex/<int:pokedex_number>", view_func=get_pokemon_by_pokedex, methods=["GET"])
    app.add_url_rule("/pokemon/by-type", view_func=list_pokemon_by_type, methods=["POST"])
    app.add_url_rule("/pokemon/<pokemon_id>", view_func=delete_pokemon, methods=["DELETE"])
