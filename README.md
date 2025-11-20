# Pokemon Scouting

## How I worded with AI to complete the case?

> Important for evaluators: Please check my Mental Map for the full development journey and decisions. So you can understand how I think: [docs/mental_map.md](docs/mental_map.md)

This is a minimal Flask application that ingests Pokemon data from PokeAPI, 
stores it in a local SQLite database using SQLAlchemy, 
and exposes simple HTTP endpoints to manage and query the data.

Key design decisions (kept intentionally simple):
- Minimal project structure with only two top-level folders: app/ and tests/ (tests mirror the app structure).
- Initial Pokemon list is loaded from a CSV file.
- An endpoint allows adding more Pokemon after the initial load.
- Pydantic for request/response schemas.
- Global JSON error handlers and request/response logging middlewares.
- Unit tests included and CI workflow running pytest on push/PR.


## How To Run Locally
Requirements:
- [Git](https://git-scm.com/downloads)
- [Python3.13](https://www.python.org/downloads/)

1. Clone the repository  
   `git clone https://github.com/salatiel6/pokemon-scouting.git`


2.  Open the challenge directory  
    Widows/Linux:`cd pokemon-scouting`  
    Mac: `open pokemon-scouting`


3. Create virtual environment (recommended)  
   `python -m venv ./venv`


4. Activate virtual environment (recommended)  
   Windows: `venv\Scripts\activate`  
   Linux/Mac: `source venv/bin/activate`


5. Install every dependencies  
   `pip install -r requirements.txt`


6. Run the application  
   `python -m app.main`

By default the app runs on http://localhost:5000.

Project structure
```
app/
  main.py                 # Flask app factory and runner
  api/
    routes.py             # Endpoints: /ingest, /add-pokemon, /pokemon, /pokemon/id/<id>, /pokemon/name/<name>, /pokemon/pokedex/<number>, /pokemon/by-type, DELETE /pokemon/<id>
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
    exceptions.py         # Exception classes used by handlers/clients
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

- GET /pokemon/id/<id>
  - Returns full details for a single Pokemon by internal id (UUID v4).

- GET /pokemon/name/<name>
  - Returns full details for a single Pokemon by canonical name (lowercase slug).

- GET /pokemon/pokedex/<number>
  - Returns full details for a single Pokemon by National Pokédex number (integer).

- POST /pokemon/by-type
  - Body: `{ "types": ["water", "ground"] }`
  - Optional query param: `limit` (default 200)
  - Returns full details for all Pokemon that match ANY of the provided types (union semantics).

- DELETE /pokemon/<id>
  - Deletes a Pokemon by id (UUID v4).
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

Tests
- Run the test suite from the project root:
```
pytest -q
```
