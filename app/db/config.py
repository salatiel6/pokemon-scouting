import csv
import os


def read_pokemon_csv(default_path: str = "app/db/pokemon_list.csv") -> list[str]:
    """
    Read an initial Pokemon list from a CSV file with a `name` column.

    :param default_path: CSV file path with a `name` header

    :return: A list of Pokemon names in lowercase
    :raises: None
    """
    if not os.path.exists(default_path):
        return []

    names: list[str] = []
    with open(default_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row:
                continue
            value = (row.get("name") or "").strip().lower()
            if value:
                names.append(value)
    return names
