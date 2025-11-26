from typing import Any

from app.models.pokemon import Pokemon


def _raw_payload(name: str, poke_id: int, types: list[str] | None = None) -> dict[str, Any]:
    """
    Build a minimal raw payload aligned with what sanitizer expects.

    :param name: canonical name returned by PokeAPI
    :param poke_id: national dex id
    :param types: optional list of type names

    :return: dict in PokeAPI format
    :raises: None
    """
    return {
        "name": name,
        "id": poke_id,
        "height": 10,
        "weight": 100,
        "base_experience": 64,
        "stats": [
            {"base_stat": 10, "stat": {"name": "hp"}},
            {"base_stat": 20, "stat": {"name": "attack"}},
            {"base_stat": 30, "stat": {"name": "defense"}},
            {"base_stat": 40, "stat": {"name": "special-attack"}},
            {"base_stat": 50, "stat": {"name": "special-defense"}},
            {"base_stat": 60, "stat": {"name": "speed"}},
        ],
        "types": [{"type": {"name": t}} for t in (types or ["electric"])],
        "abilities": [{"ability": {"name": "static"}}],
    }


def test_add_and_list_and_get_delete_flow(app, client, monkeypatch) -> None:
    """
    Full flow: add via POST /add-pokemon, list via GET /pokemon, get by id and name, then delete.

    :param app: Flask app fixture
    :param client: Flask client fixture
    :param monkeypatch: pytest monkeypatch

    :return: None
    :raises: None
    """

    # Patch upstream client to return controlled payloads
    def fake_get(name: str):  # type: ignore[no-redef]
        mapping = {
            "pikachu": _raw_payload("pikachu", 25, ["electric"]),
            "bulbasaur": _raw_payload("bulbasaur", 1, ["grass", "poison"]),
        }
        if name in mapping:
            return mapping[name]
        from app.handlers.pokeapi_client import PokemonNotFoundError

        raise PokemonNotFoundError(name)

    import app.handlers.pokeapi_client as client_mod

    monkeypatch.setattr(client_mod.PokeAPIClient, "get_pokemon_by_name", staticmethod(fake_get))

    # Add mixed names: one ok, one unknown
    resp = client.post("/pokemon", json={"names": ["pikachu", "unknown"]})
    assert resp.status_code == 202
    data = resp.get_json()
    assert data["ok"] == ["pikachu"]
    assert data["not_found"] == ["unknown"]
    assert data["errors"] == []

    # Add another valid one
    resp = client.post("/pokemon", json={"names": ["bulbasaur"]})
    assert resp.status_code == 202

    # List with default limit (200) includes both with full details
    resp = client.get("/pokemon")
    assert resp.status_code == 200
    items = resp.get_json()
    assert isinstance(items, list)
    assert len(items) == 2
    for item in items:
        assert set(
            ["id", "name", "pokedex_number", "height_m", "weight_kg", "base_experience", "stats", "types", "abilities"]
        ).issubset(item.keys())

    # List with limit=1 only returns one
    resp = client.get("/pokemon?limit=1")
    assert resp.status_code == 200
    items = resp.get_json()
    assert len(items) == 1

    # Get by name returns full details
    resp = client.get("/pokemon/name/pikachu")
    assert resp.status_code == 200
    pikachu = resp.get_json()
    assert pikachu["name"] == "pikachu"
    assert pikachu["pokedex_number"] == 25

    # Get by id (UUID). Fetch ID from database
    p = Pokemon.query.filter_by(name="pikachu").first()
    assert p is not None
    resp = client.get(f"/pokemon/id/{p.id}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == p.id

    # Get by pokedex number
    resp = client.get("/pokemon/pokedex/25")
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "pikachu"

    # Delete by id
    resp = client.delete(f"/pokemon/{p.id}")
    assert resp.status_code == 204

    # Subsequent get returns 404
    resp = client.get(f"/pokemon/id/{p.id}")
    assert resp.status_code == 404


def test_validation_error_returns_400(client) -> None:
    """
    Ensure that invalid request body triggers Pydantic ValidationError -> 400 via handler.

    :param client: Flask client

    :return: None
    :raises: None
    """
    # names must be a list; send an object to cause validation error
    resp = client.post("/pokemon", json={"names": {"bad": "format"}})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "validation_error"


def test_list_by_type_union(app, client, monkeypatch) -> None:
    """
    Verify that POST /pokemon/by-type returns union of matches.

    :param app: Flask app fixture
    :param client: Flask client fixture
    :param monkeypatch: pytest monkeypatch

    :return: None
    :raises: None
    """

    # Patch upstream client to return controlled payloads
    def fake_get(name: str):  # type: ignore[no-redef]
        mapping = {
            "pikachu": _raw_payload("pikachu", 25, ["electric"]),
            "swampert": _raw_payload("swampert", 260, ["water", "ground"]),
            "bulbasaur": _raw_payload("bulbasaur", 1, ["grass", "poison"]),
        }
        if name in mapping:
            return mapping[name]
        from app.handlers.pokeapi_client import PokemonNotFoundError

        raise PokemonNotFoundError(name)

    import app.handlers.pokeapi_client as client_mod

    monkeypatch.setattr(client_mod.PokeAPIClient, "get_pokemon_by_name", staticmethod(fake_get))

    # Ingest three
    resp = client.post("/pokemon", json={"names": ["pikachu", "swampert", "bulbasaur"]})
    assert resp.status_code == 202

    # Filter by one type 'water' should include swampert
    resp = client.post("/pokemon/by-type", json={"types": ["water"]})
    assert resp.status_code == 200
    names = sorted([x["name"] for x in resp.get_json()])
    assert "swampert" in names

    # Filter by 'ground' also returns swampert
    resp = client.post("/pokemon/by-type", json={"types": ["ground"]})
    assert resp.status_code == 200
    names = sorted([x["name"] for x in resp.get_json()])
    assert "swampert" in names

    # Filter by both 'water' and 'ground' still includes swampert (union)
    resp = client.post("/pokemon/by-type", json={"types": ["water", "ground"]})
    assert resp.status_code == 200
    names = sorted([x["name"] for x in resp.get_json()])
    assert "swampert" in names
