from datetime import UTC, datetime, timedelta
from typing import Any, Iterable

from sqlalchemy import ColumnElement

from app.db import db
from app.handlers.cache import cache_get, cache_set
from app.handlers.config import settings
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
            base_url = settings.POKEAPI_BASE_URL
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
                # DB-first: if record exists and is not stale, skip upstream call
                existing = Pokemon.query.filter_by(name=str(name).lower()).one_or_none()
                if existing is not None and not self._is_stale(existing):
                    logger.debug(f"db-first: fresh record, skipping fetch for {existing.name}")
                    results["ok"].append(existing.name)
                    continue

                # Cache-first for upstream payload
                norm = "".join(ch for ch in str(name).strip().lower() if ch.isalnum())
                cache_key = f"pokeapi:{norm}"
                raw = cache_get(cache_key)
                if raw is None:
                    raw = self.client.get_pokemon_by_name(name)
                    # Use default cache timeout from settings
                    cache_set(cache_key, raw, timeout=int(settings.CACHE_DEFAULT_TIMEOUT))

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

        # Update freshness timestamp
        p.refreshed_at = datetime.now(UTC)

        db.session.add(p)

    @staticmethod
    def _is_stale(pokemon: Pokemon) -> bool | ColumnElement[bool]:
        """
        Check if a Pokemon row is stale based on app configuration TTL.

        :param pokemon: Pokemon ORM instance

        :return: True if stale or never refreshed, False if fresh
        """
        minutes = int(settings.STALE_TTL_MINUTES)
        refreshed = pokemon.refreshed_at

        if refreshed is None:
            return True

        if refreshed.tzinfo is None:
            refreshed = refreshed.replace(tzinfo=UTC)

        cutoff = datetime.now(UTC) - timedelta(minutes=minutes)
        return refreshed < cutoff
