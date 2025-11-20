import uuid

from sqlalchemy import Float, Integer, String
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db import db


class Pokemon(db.Model):
    """
    Core Pokemon model persisted in a single table with JSON fields.

    Columns:
    - id: UUID v4 (string) primary key.
    - name: unique lowercase name from PokeAPI.
    - pokedex_number: integer National Pokedex number (not unique to allow forms/mega evolutions).
    - height_m, weight_kg: floats with units converted from PokeAPI.
    - base_experience: integer, optional.
    - stats: JSON dict {"hp": int, ...}.
    - types: JSON list[str].
    - abilities: JSON list[str].
    """

    __tablename__ = "pokemon"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    pokedex_number: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    height_m: Mapped[float] = mapped_column(Float, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    base_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stats: Mapped[dict[str, int]] = mapped_column(SQLITE_JSON, nullable=False)

    types: Mapped[list[str]] = mapped_column(SQLITE_JSON, nullable=False, default=list)
    abilities: Mapped[list[str]] = mapped_column(SQLITE_JSON, nullable=False, default=list)
