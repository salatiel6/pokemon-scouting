from typing import Any, Iterable

from flask import current_app

from app.db import db
from app.handlers.logger import logger
from app.handlers.pokeapi_client import (
    PokeAPIClient,
    PokemonNotFoundError,
)
from app.handlers.sanitizer import sanitize_pokemon_data
from app.models.pokemon import Pokemon


class IngestService:
    """
    Service responsible for fetching, transforming and persisting Pokemon data.
    """

    def __init__(self, base_url: str | None = None) -> None:
        """
        Initialize the ingestion service with a PokeAPI client.

        :param base_url: Optional PokeAPI base URL; defaults to app config

        :return: None
        """
        if base_url is None:
            base_url = current_app.config.get("POKEAPI_BASE_URL", "https://pokeapi.co/api/v2")
        self.client = PokeAPIClient(str(base_url))

    def ingest_many(self, names: Iterable[str]) -> dict[str, Any]:
        """
        Ingest many Pokemon by names, performing upserts in the database.

        :param names: an iterable of Pokemon names

        :return: Summary dict
        """
        results: dict[str, Any] = {"ok": [], "not_found": [], "errors": []}

        for name in names:
            try:
                raw = self.client.get_pokemon_by_name(name)
                data = sanitize_pokemon_data(raw)
                self._upsert(data)
                results["ok"].append(data["name"])
            except PokemonNotFoundError as e:
                logger.error(f"Pokemon not found: {e}")
                results["not_found"].append(name)
            except Exception as e:
                logger.error(f"Error ingesting Pokemon {name}: {e}")
                results["errors"].append({"name": name, "error": str(e)})

        db.session.commit()
        return results

    @staticmethod
    def _upsert(data: dict[str, Any]) -> None:
        """
        Create or update a Pokemon and its relations based on sanitized data.

        :param data: a dict produced by sanitize_pokemon_data()

        :return: None
        """
        p = Pokemon.query.filter_by(name=data["name"]).one_or_none()
        if not p:
            p = Pokemon()
            p.pokedex_number = data["pokedex_number"]
            p.name = data["name"]

        # Update scalar fields
        p.name = data["name"]
        p.height_m = data["height_m"]
        p.weight_kg = data["weight_kg"]
        p.base_experience = data.get("base_experience")
        p.stats = data["stats"]
        p.pokedex_number = data["pokedex_number"]

        # JSON list fields
        p.types = list(data.get("types") or [])
        p.abilities = list(data.get("abilities") or [])

        db.session.add(p)
