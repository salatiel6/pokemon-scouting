from typing import Any

from app.schemas.pokemon import STAT_KEYS


def _extract_stats(raw_stats: list[dict[str, Any]]) -> dict[str, int]:
    """
    Extract base stats from PokeAPI raw payload list.

    :param raw_stats: a list of stat objects from PokeAPI

    :return: dict with canonical stat keys and integer values
    """
    stats: dict[str, int] = {k: 0 for k in STAT_KEYS}
    for item in raw_stats or []:
        name = (item.get("stat") or {}).get("name")
        base = int(item.get("base_stat", 0) or 0)
        if name in STAT_KEYS:
            stats[name] = base
    return stats


def sanitize_pokemon_data(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Transform PokeAPI JSON into a normalized dictionary ready for persistence.

    :param raw: a dict with the raw PokeAPI pokemon payload

    :return: A normalized dict
    """
    name = str(raw.get("name", "")).lower()
    types = [t["type"]["name"].lower() for t in (raw.get("types") or [])]
    abilities = [a["ability"]["name"].lower() for a in (raw.get("abilities") or [])]

    pokedex_id = raw.get("id")
    if pokedex_id is None:
        raise ValueError("Missing 'id' in PokeAPI payload")

    base_experience_raw = raw.get("base_experience")

    return {
        "name": name,
        "pokedex_number": int(pokedex_id),
        "height_m": float(raw.get("height", 0) or 0) / 10.0,
        "weight_kg": float(raw.get("weight", 0) or 0) / 10.0,
        "base_experience": int(base_experience_raw) if base_experience_raw is not None else None,
        "stats": _extract_stats(raw.get("stats") or []),
        "types": types,
        "abilities": abilities,
    }
