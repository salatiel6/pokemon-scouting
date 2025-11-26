from typing import Any

from flask import Blueprint, jsonify, request

from app.db import db
from app.handlers.ingest_service import IngestService
from app.handlers.logger import logger
from app.models.pokemon import Pokemon
from app.schemas.pokemon import (
    IngestResult,
    PokemonDetail,
    PokemonIngestRequest,
    TypesFilterRequest,
)

pokemon_bp = Blueprint("pokemon", __name__, url_prefix="/pokemon")


def _to_detail_dict(pokemon: Pokemon) -> dict:
    """
    Convert a Pokemon ORM instance to a full detail dictionary using the
    PokemonDetail schema to ensure a consistent shape.

    :param pokemon: a Pokemon ORM instance

    :return: A dict with full Pokemon details
    """
    detail = PokemonDetail.model_validate(pokemon)
    return detail.model_dump()


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
    List Pokemon resources with optional name filter and limit.

    :return: A JSON array of full PokemonDetail objects
    """
    logger.info("Listing Pokemon...")

    query = Pokemon.query
    name_filter = request.args.get("name")
    if name_filter:
        query = query.filter(Pokemon.name.ilike(f"%{name_filter}%"))

    limit = request.args.get("limit", default=200, type=int)
    if not isinstance(limit, int) or limit <= 0:
        limit = 200

    items = [_to_detail_dict(pokemon) for pokemon in query.limit(limit).all()]

    return jsonify(items)


def get_pokemon_by_id(pokemon_id: str) -> tuple[Any, int] | Any:
    """
    Retrieve a single Pokemon by internal ID.

    :param pokemon_id: Pokemon UUID identifier

    :return: PokemonDetail JSON or 404
    """
    logger.info("Retrieving Pokemon by ID...")

    pokemon = Pokemon.query.filter_by(id=pokemon_id).first()
    if not pokemon:
        return jsonify({"error": "not_found"}), 404

    return jsonify(_to_detail_dict(pokemon))


def get_pokemon_by_name(name: str) -> tuple[Any, int] | Any:
    """
    Retrieve a single Pokemon by canonical name.

    :param name: Pokemon canonical name

    :return: PokemonDetail JSON or 404
    """
    logger.info("Retrieving Pokemon by name...")

    pokemon = Pokemon.query.filter_by(name=name.lower()).first()
    if not pokemon:
        return jsonify({"error": "not_found"}), 404

    return jsonify(_to_detail_dict(pokemon))


def get_pokemon_by_pokedex(pokedex_number: int) -> tuple[Any, int] | Any:
    """
    Retrieve a single Pokemon by National Pokedex number.

    :param pokedex_number: integer Pokedex number

    :return: PokemonDetail JSON or 404
    """
    logger.info("Retrieving Pokemon by Pokédex number...")

    pokemon = Pokemon.query.filter_by(pokedex_number=int(pokedex_number)).first()
    if not pokemon:
        return jsonify({"error": "not_found"}), 404

    return jsonify(_to_detail_dict(pokemon))


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

    for pokemon in Pokemon.query.all():
        pokemon_types = set(pokemon.types or [])
        if pokemon_types.intersection(wanted):
            matches.append(pokemon)
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

    pokemon = Pokemon.query.filter_by(id=pokemon_id).first()

    if not pokemon:
        return jsonify({"error": "not_found"}), 404

    db.session.delete(pokemon)
    db.session.commit()
    return "", 204


def register_pokemon_routes() -> None:
    """
    Register all Pokemon-related routes on the pokemon blueprint.

    :return: None
    :raises: None
    """
    # Official RESTful create/list endpoints
    pokemon_bp.add_url_rule("", view_func=add_pokemon, methods=["POST"])  # /pokemon
    pokemon_bp.add_url_rule("", view_func=list_pokemon, methods=["GET"])  # /pokemon
    # Query endpoints
    pokemon_bp.add_url_rule("/id/<pokemon_id>", view_func=get_pokemon_by_id, methods=["GET"])
    pokemon_bp.add_url_rule("/name/<name>", view_func=get_pokemon_by_name, methods=["GET"])
    pokemon_bp.add_url_rule("/pokedex/<int:pokedex_number>", view_func=get_pokemon_by_pokedex, methods=["GET"])
    pokemon_bp.add_url_rule("/by-type", view_func=list_pokemon_by_type, methods=["POST"])
    # Delete endpoint
    pokemon_bp.add_url_rule("/<pokemon_id>", view_func=delete_pokemon, methods=["DELETE"])


# Register routes when module is imported
register_pokemon_routes()
