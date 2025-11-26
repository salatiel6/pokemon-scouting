# Pokemon Scouting

## How I used AI to complete the case?

> Important for evaluators: Please check the Mental Map for the full development journey and decisions: [docs/mental_map.md](docs/mental_map.md)

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
- DB-first ingestion with in-memory caching and a background refresh job to reduce latency and keep data fresh.


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


6. Configure environment
   - Copy the example file and adjust values as needed:
   - The values are available only because this is a test
   - On normal cases `.env` values should be private
     - `cp .env.example .env`

7. Run the application  
   `python -m app.main`

By default the app runs on http://localhost:5000.

## Run with Docker

This repository ships with a ready-to-use Docker setup for isolated execution.

Steps:
1) Copy the env file (optional, recommended):
```
cp .env.example .env
```
2) Build and start the container:
```
docker compose up --build
```
3) The API will be available at:
```
http://localhost:5000
```

Notes:
- Environment variables are loaded from `.env` by docker-compose (env_file). You can tweak cache, sync interval, etc., there.
- By default inside the container the SQLite DB lives at `sqlite:///instance/pokemon.db`. To persist it on the host, uncomment the `volumes` section in `docker-compose.yaml` and optionally set `SQLALCHEMY_DATABASE_URI=sqlite:///instance/pokemon.db` (already defaulted in the Dockerfile runtime stage).
- If `SYNC_ON_START=true`, on the first boot the app will ingest the initial CSV list from `app/db/pokemon_list.csv`.

Quick curl examples (while container is running):
- Healthcheck:
```
curl http://localhost:5000/health
```
- Ingest a Pokemon:
```
curl -X POST http://localhost:5000/pokemon \
  -H 'Content-Type: application/json' \
  -d '{"names":["pikachu"]}'
```
- List Pokemons (limit 5):
```
curl 'http://localhost:5000/pokemon?limit=5'
```
- Get by name:
```
curl http://localhost:5000/pokemon/name/pikachu
```
- Filter by type:
```
curl -X POST http://localhost:5000/pokemon/by-type \
  -H 'Content-Type: application/json' \
  -d '{"types":["water","ground"]}'
```

Project structure
```
app/
  main.py                 # Flask app factory and runner
  api/
    pokemon.py            # Blueprint 'pokemon' (prefix /pokemon):
                          #   /pokemon (GET, POST)
                          #   /pokemon/id/<id>
                          #   /pokemon/name/<name>
                          #   /pokemon/pokedex/<number>
                          #   /pokemon/by-type (POST)
                          #   DELETE /pokemon/<id>
    health.py             # Blueprint 'health': /health
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
Dockerfile                # Multi-stage build (builder + runtime)
docker-compose.yaml       # Simple compose with web service and env_file mapping
.dockerignore             # Slim build context
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

Configuration via .env
- The app automatically loads `.env` if present (using python-dotenv). All variables are optional and have defaults.
- Keys you can set:
  - `SQLALCHEMY_DATABASE_URI` (default `sqlite:///pokemon.db`)
  - `POKEAPI_BASE_URL` (default `https://pokeapi.co/api/v2`)
  - `SYNC_ON_START` (default `true`)
  - `CACHE_TYPE` (default `SimpleCache`)
  - `CACHE_DEFAULT_TIMEOUT` (default `1800` seconds)
  - `STALE_TTL_MINUTES` (default `30`)
  - `DISABLE_BACKGROUND_SYNC` (default `false`)
  - `SYNC_INTERVAL_MINUTES` (default `30`)
  - `REFRESH_BATCH_SIZE` (default `20`)
  
Tip: For local development when running tests or avoiding network calls, consider setting:
```
SYNC_ON_START=false
DISABLE_BACKGROUND_SYNC=true
```

Input rule for names (important)
- When calling POST /pokemon, always send Pokemon names in lowercase and without any symbols (no spaces, hyphens, dots, etc.).
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
- GET /health
  - Simple healthcheck endpoint. Returns `{ "status": "ok" }`.

- POST /pokemon
  - Body: `{ "names": ["bulbasaur"] }`
  - Behavior: DB-first + cache-first. If the Pokemon already exists in DB and is fresh (not stale by `STALE_TTL_MINUTES`), PokeAPI is not called. Otherwise, it uses cache; on miss, fetches from PokeAPI and caches the raw payload.
  - Response: `{ "ok": [...], "not_found": [...], "errors": [{"name": ..., "error": ...}] }`
  - Note: Deprecated alias still available temporarily: `POST /add-pokemon`.

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

Startup sync (replaces /ingest)
- On application startup, when `SYNC_ON_START=true` (default), the app will read `app/db/pokemon_list.csv` and ingest those Pokemons automatically using the same ingestion flow as the API.
- Network failures or upstream issues are logged as warnings and do not prevent the application from starting.

Caching and background refresh
- Caching: the app uses Flask-Caching `SimpleCache` by default. Upstream PokeAPI payloads are cached under keys like `pokeapi:{normalized_name}` for `CACHE_DEFAULT_TIMEOUT` seconds.
- DB-first: if a requested Pokemon exists in DB and was refreshed within `STALE_TTL_MINUTES`, ingestion skips PokeAPI to reduce latency.
- Background refresh: an APScheduler BackgroundScheduler runs every `SYNC_INTERVAL_MINUTES` to refresh a small batch (`REFRESH_BATCH_SIZE`) of stale/never-refreshed rows. Set `DISABLE_BACKGROUND_SYNC=true` to disable.
