from typing import Any

from app.handlers.ingest_service import IngestService
from app.handlers.pokeapi_client import PokemonNotFoundError
from app.models.pokemon import Pokemon


def _raw_payload(name: str, poke_id: int) -> dict[str, Any]:
    """
    Build a minimal raw payload similar to PokeAPI response for tests.

    :param name: Pokemon name (canonical)
    :param poke_id: National Pokédex ID

    :return: A dict shaped like PokeAPI's pokemon resource
    :raises: None
    """
    return {
        "name": name,
        "id": poke_id,
        "height": 10,
        "weight": 100,
        "base_experience": 64,
        "stats": [
            {"base_stat": 45, "stat": {"name": "hp"}},
            {"base_stat": 49, "stat": {"name": "attack"}},
            {"base_stat": 49, "stat": {"name": "defense"}},
            {"base_stat": 65, "stat": {"name": "special-attack"}},
            {"base_stat": 65, "stat": {"name": "special-defense"}},
            {"base_stat": 45, "stat": {"name": "speed"}},
        ],
        "types": [{"type": {"name": "grass"}}, {"type": {"name": "poison"}}],
        "abilities": [{"ability": {"name": "overgrow"}}],
    }


def test_ingest_service_upsert_and_summary(monkeypatch, app) -> None:
    """
    Verify that IngestService ingests valid names, reports not_found, and persists rows.

    :param monkeypatch: pytest monkeypatch fixture
    :param app: Flask test app

    :return: None
    :raises: None
    """

    def fake_get(name: str):  # type: ignore[no-redef]
        if name == "bulbasaur":
            return _raw_payload("bulbasaur", 1)
        raise PokemonNotFoundError(name)

    # Patch the PokeAPI client method used by the service
    import app.handlers.pokeapi_client as client_mod

    monkeypatch.setattr(client_mod.PokeAPIClient, "get_pokemon_by_name", staticmethod(fake_get))

    service = IngestService(base_url="https://example.com/api/v2")
    # Ensure DB session has an active app context during commit
    with app.app_context():
        result = service.ingest_many(["bulbasaur", "doesnotexist"])

    assert result["ok"] == ["bulbasaur"]
    assert result["not_found"] == ["doesnotexist"]
    assert result["errors"] == []

    # Check DB persisted entity
    with app.app_context():
        p = Pokemon.query.filter_by(name="bulbasaur").first()
        assert p is not None
        assert p.pokedex_number == 1
        assert p.height_m == 1.0
        assert p.weight_kg == 10.0
        assert p.stats["hp"] == 45
        assert "grass" in p.types and "poison" in p.types
        assert "overgrow" in p.abilities
