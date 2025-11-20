class PokeAPIError(Exception):
    """Base exception for PokeAPI client errors."""


class PokemonNotFoundError(PokeAPIError):
    """Error raised when a Pokemon resource is not found (HTTP 404)."""
