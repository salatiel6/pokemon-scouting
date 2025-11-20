from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PokemonIngestRequest(BaseModel):
    """Request body schema for ingesting Pokemon names."""

    names: list[str] = Field(default_factory=list, description="list of Pokemon names")

    @field_validator("names")
    @classmethod
    def _normalize(cls, v: list[str]) -> list[str]:
        """
        Normalize names to the required input rule: lowercase and no symbols.

        All non-alphanumeric characters are removed and the string is lowercased.

        :param v: a list of strings

        :return: Normalized list (lowercase, alphanumeric only), empty entries removed
        """
        norm: list[str] = []
        for x in v:
            s = str(x).strip().lower()
            s = "".join(ch for ch in s if ch.isalnum())
            if s:
                norm.append(s)
        return norm


class PokemonSummary(BaseModel):
    """Summary representation for listing Pokemon."""

    id: str
    name: str
    pokedex_number: int
    types: list[str] = Field(default_factory=list)


class PokemonDetail(BaseModel):
    """Detailed representation of a Pokemon resource."""

    id: str
    name: str
    pokedex_number: int
    height_m: float
    weight_kg: float
    base_experience: Optional[int] = None
    stats: dict[str, int]
    types: list[str]
    abilities: list[str]

    model_config = ConfigDict(from_attributes=True)


class IngestResult(BaseModel):
    """Result summary for an ingestion run."""

    ok: list[str] = Field(default_factory=list)
    not_found: list[str] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)
