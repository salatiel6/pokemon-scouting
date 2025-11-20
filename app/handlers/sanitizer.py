from typing import Any


STAT_KEYS = {
    "hp",
    "attack",
    "defense",
    "special-attack",
    "special-defense",
    "speed",
}


def _extract_stats(raw_stats: list[dict[str, Any]]) -> dict[str, int]:
    """
    Extract base stats from PokeAPI raw payload list.

    :param raw_stats: a list of stat objects from PokeAPI

    :return: dict with canonical stat keys and integer values
    :raises: None
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
    :raises: None
    """
    name = str(raw.get("name", "")).lower()
    types = [t["type"]["name"].lower() for t in (raw.get("types") or [])]
    abilities = [a["ability"]["name"].lower() for a in (raw.get("abilities") or [])]

    return {
        "name": name,
        "pokedex_number": int(raw.get("id")),
        "height_m": float(raw.get("height", 0) or 0) / 10.0,
        "weight_kg": float(raw.get("weight", 0) or 0) / 10.0,
        "base_experience": int(raw.get("base_experience")) if raw.get("base_experience") is not None else None,
        "stats": _extract_stats(raw.get("stats") or []),
        "types": types,
        "abilities": abilities,
    }
