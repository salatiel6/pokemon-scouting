# Pokemon Scouting

> Important for evaluators: How I used AI to complete the case?
>
> Please check the Mental Map for the full development journey with AI and decisions: [docs/mental_map.md](docs/mental_map.md)

This is a minimal Flask application that ingests Pokemon data from PokeAPI, stores it in a local SQLite database using SQLAlchemy, and exposes simple HTTP endpoints to manage and query the data.

Key design decisions (kept intentionally simple):
- Minimal project structure with only two top-level folders: app/ and tests/ (tests mirror the app structure).
- Initial Pokemon list is loaded from a CSV file.
- An endpoint allows adding more Pokemon after the initial load.
- No blueprints, simple route registration.
- Pydantic for request/response schemas.
- Global JSON error handlers and request/response logging middlewares.
- Unit tests included and CI workflow (GitHub Actions) running pytest on push/PR.

Requirements
- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

Project structure
```
app/
  main.py                 # Flask app factory and runner
  api/
    routes.py             # Endpoints: /ingest, /add-pokemon, /pokemon, /pokemon/<id_or_name>
  models/
    __init__.py
    pokemon.py            # SQLAlchemy model: single-table Pokemon with JSON fields
  handlers/
    __init__.py
    pokeapi_client.py     # HTTP client for PokeAPI
    sanitizer.py          # Transforms PokeAPI payload to internal schema
    ingest_service.py     # Orchestrates fetch → sanitize → upsert
    errors.py             # Global error handlers (ValidationError, DB, upstream, etc.)
    middlewares.py        # Request/response logging middlewares
    logger.py             # Centralized logger configuration
  schemas/
    __init__.py
    pokemon.py            # Pydantic schemas for requests/responses
  db/
    __init__.py           # SQLAlchemy initialization (create_all)
    config.py             # CSV reader utility
    pokemon_list.csv      # Initial seed list of Pokemon names
tests/                    # Unit tests mirroring app/
  conftest.py
  test_api/
    test_routes.py
  test_handlers/
    test_ingest_service.py
    test_pokeapi_client.py
    test_sanitizer.py
  test_schemas/
    test_pokemon.py
.github/
  workflows/
    tests.yml             # CI workflow running pytest on push/PR
requirements.txt
README.md
```

Run the app
1. Create a virtual environment and install requirements.
2. Start the server:
```
python -m app.main
```
By default the app runs on http://localhost:5000.

Configuration
- SQLALCHEMY_DATABASE_URI: defaults to `sqlite:///pokemon.db` in the project root.
- POKEAPI_BASE_URL: defaults to `https://pokeapi.co/api/v2`.

Input rule for names (important)
- When calling POST /ingest or /add-pokemon, always send Pokemon names in lowercase and without any symbols (no spaces, hyphens, dots, etc.).
- The API normalizes input to this format and uses a built-in alias map to resolve tricky cases to PokeAPI’s canonical slugs (e.g., `mrmime` → `mr-mime`, `mewtwo` → `MewTwo`, `typenull` → `type-null`).

CSV initial load
- File: `app/db/pokemon_list.csv`
- Format: a header `name` and one Pokemon name per line, e.g.:
```
name
pikachu
dhelmise
charizard
parasect
aerodactyl
kingler
```

HTTP endpoints
- POST /ingest
  - Body: `{ "names": ["pikachu", "charizard"] }` (optional). If omitted or empty, the CSV is used.
  - Response: `{ "ok": [...], "not_found": [...], "errors": [{"name": ..., "error": ...}] }`

- POST /add-pokemon
  - Body: `{ "names": ["bulbasaur"] }`
  - Response: same format as /ingest

- GET /pokemon
  - Optional query params:
    - `name` for partial match (e.g., `?name=pika`).
    - `limit` (default: 200) to control number of results.
  - Returns an array of full details for each Pokemon.
  - Note: `id` is a UUID v4 string.

- GET /pokemon/<id_or_name>
  - Returns full details for a single Pokemon.

- DELETE /pokemon/<id_or_name>
  - Deletes a Pokemon by id (UUID) or by name.
  - Returns 204 on success or 404 if not found.

Data model (single table)
- Pokemon table:
  - `id` (UUID v4, string, primary key)
  - `name` (unique, lowercase string)
  - `pokedex_number` (int, indexed)
  - `height_m` (float)
  - `weight_kg` (float)
  - `base_experience` (int, nullable)
  - `stats` (JSON object: {"hp": int, "attack": int, ...})
  - `types` (JSON array of strings)
  - `abilities` (JSON array of strings)

Notes
- This is a simple case test. No Alembic migrations were added; tables are created on startup if they do not exist.
- Error handlers and logging middlewares are registered automatically during app startup.

ID policy
- The primary key `id` of the `pokemon` table is now a UUID v4 (string). We no longer use the Pokédex number as the primary key to allow multiple forms/mega evolutions sharing the same `pokedex_number`.
- If you previously ran the app with the old schema, delete the existing SQLite file (e.g., `pokemon.db`) before re-ingesting so new records use the updated schema and IDs.

Tests
- Run the test suite from the project root:
```
pytest -q
```

Continuous Integration
- This repository includes a GitHub Actions workflow that runs the tests on every push and pull request.
- File: `.github/workflows/tests.yml`