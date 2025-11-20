from typing import Any

import requests

from app.handlers.exceptions import PokeAPIError, PokemonNotFoundError
from app.handlers.logger import logger
from app.schemas.pokemon import POKEMON_ALIASES


class PokeAPIClient:
    """
    Simple HTTP client for PokeAPI v2 endpoints that resolves known lowercase
    alias inputs to canonical PokeAPI slugs before requesting.
    """

    def __init__(self, base_url: str, timeout_s: float = 10.0) -> None:
        """
        Initialize the client with a base URL and timeout.

        :param base_url: Base URL for PokeAPI
        :param timeout_s: Request timeout in seconds

        :return: None
        """
        self.base_url = base_url.rstrip("/")
        self.timeout_s = float(timeout_s)

    def get_pokemon_by_name(self, name: str) -> dict[str, Any]:
        """
        Fetch a Pokemon resource by its name using alias mapping only.

        The user input must be lowercase without spaces/hyphens/punctuation.
        If the normalized input matches an alias key, it is replaced by the
        canonical PokeAPI name before the request. Otherwise, the input is
        used as provided.

        :param name: Pokemon name as provided by the user

        :return: Raw JSON payload as a dictionary
        :raises: PokemonNotFoundError if not found; PokeAPIError for other errors
        """
        raw = str(name or "").strip()

        normalized = "".join(ch for ch in raw.lower() if ch.isalnum())
        name = POKEMON_ALIASES.get(normalized, raw)
        data = self._try_fetch(name)
        if data is None:
            raise PokemonNotFoundError(
                f"Pokemon not found for input '{name}'. If you provided a raw lowercase name, "
                f"please verify it against PokeAPI's canonical name."
            )
        return data

    def _try_fetch(self, name: str) -> dict[str, Any] | None:
        """
        Try to fetch a Pokemon by a given slug. Returns None on 404.

        :param name: A candidate slug to append to /pokemon/

        :return: JSON dict on success, or None if the response was 404
        :raises: PokeAPIError for non-404 HTTP errors or request failures
        """
        url = f"{self.base_url}/pokemon/{name}"
        try:
            resp = requests.get(url, timeout=self.timeout_s)
        except requests.RequestException as e:
            logger.error(f"request error: {e}")
            raise PokeAPIError(f"network error: {e}") from e

        if resp.status_code == 404:
            return None
        if not resp.ok:
            raise PokeAPIError(f"status {resp.status_code}: {resp.text}")
        return resp.json()
