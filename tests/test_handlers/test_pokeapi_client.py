from typing import Any

import pytest

from app.handlers.pokeapi_client import PokeAPIClient, PokemonNotFoundError


class DummyResp:
    def __init__(self, status_code: int, json_data: dict[str, Any] | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> dict[str, Any]:
        return self._json


def test_alias_mapping_mrmime(monkeypatch) -> None:
    """
    Ensure alias 'mrmime' resolves to 'mr-mime' and performs the request on that slug.

    :param monkeypatch: pytest monkeypatch fixture

    :return: None
    :raises: None
    """
    called = {"url": None}

    def fake_get(url: str, timeout: float):  # type: ignore[no-redef]
        called["url"] = url
        return DummyResp(
            200, {"name": "mr-mime", "id": 122, "height": 13, "weight": 545, "stats": [], "types": [], "abilities": []}
        )

    import requests

    monkeypatch.setattr(requests, "get", fake_get)

    client = PokeAPIClient(base_url="https://example.com/api/v2")
    data = client.get_pokemon_by_name("mrmime")
    assert data["name"] == "mr-mime"
    assert called["url"] == "https://example.com/api/v2/pokemon/mr-mime"


def test_not_found_raises(monkeypatch) -> None:
    """
    Ensure 404 from upstream is converted into PokemonNotFoundError.

    :param monkeypatch: pytest monkeypatch fixture

    :return: None
    :raises: None
    """

    def fake_get(url: str, timeout: float):  # type: ignore[no-redef]
        return DummyResp(404)

    import requests

    monkeypatch.setattr(requests, "get", fake_get)

    client = PokeAPIClient(base_url="https://example.com/api/v2")
    with pytest.raises(PokemonNotFoundError):
        client.get_pokemon_by_name("doesnotexist")
