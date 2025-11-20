from app.handlers.sanitizer import sanitize_pokemon_data


def test_sanitize_pokemon_data_transforms_units_and_lists() -> None:
    """
    Ensure sanitizer converts decimeters to meters, hectograms to kg,
    extracts stats into a dict, and lowercases lists for types/abilities.

    :return: None
    :raises: None
    """
    raw = {
        "name": "Pikachu",
        "id": 25,
        "height": 4,  # dm
        "weight": 60,  # hg
        "base_experience": 112,
        "stats": [
            {"base_stat": 35, "stat": {"name": "hp"}},
            {"base_stat": 55, "stat": {"name": "attack"}},
            {"base_stat": 40, "stat": {"name": "defense"}},
            {"base_stat": 50, "stat": {"name": "special-attack"}},
            {"base_stat": 50, "stat": {"name": "special-defense"}},
            {"base_stat": 90, "stat": {"name": "speed"}},
        ],
        "types": [{"type": {"name": "Electric"}}],
        "abilities": [
            {"ability": {"name": "Static"}},
            {"ability": {"name": "Lightning-rod"}},
        ],
    }

    data = sanitize_pokemon_data(raw)
    assert data["name"] == "pikachu"
    assert data["pokedex_number"] == 25
    assert data["height_m"] == 0.4
    assert data["weight_kg"] == 6.0
    assert data["base_experience"] == 112
    assert data["stats"]["hp"] == 35
    assert data["types"] == ["electric"]
    assert data["abilities"] == ["static", "lightning-rod"]
