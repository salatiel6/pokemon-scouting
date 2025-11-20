# Mental Map: How I used AI to complete the case

This is my mental map describing how I used an AI assistant to design and implement a minimal Pokemon Scouting app. It focuses on my requests, the AI’s suggestions, my decisions, and the reasoning that led to the final, working result.

## 1) I asked for a full plan, got overengineering, and steered to minimalism
- I started by showing the case and asking the AI for a complete plan (directory layout and code snippets).
- The AI delivered a very layered/enterprise-style plan (Blueprints, repositories, migrations…). I felt it was overengineering for a case test.
- I set clear constraints: only two folders at the root (`app/` and `tests/`). Inside `app/`, the folders should be `api/`, `models/`, `handlers/`, `schemas/`, `db/`, and `main.py`. Endpoints must be simple (no blueprints). Handlers contain everything that isn’t a route. Schemas use Pydantic. DB config is simple (SQLite), no Alembic. I also wanted to discuss how to add new Pokemons easily (CSV vs endpoint).
- The AI simplified the plan accordingly.

## 2) We aligned on a minimal architecture
- `app/main.py`: create the Flask app, basic config, init DB, register routes, middlewares, and error handlers.
- `app/api/routes.py`: functions at module level; `register_routes(app)` only registers them (no nested functions).
- `app/models/pokemon.py`: ORM model (we later converged to a single-table design with JSON fields).
- `app/handlers/`: PokeAPI client, ingestion service, sanitizer, plus middlewares and error handlers.
- `app/schemas/`: Pydantic schemas for requests and responses.
- `app/db/`: SQLAlchemy initialization and CSV reader for initial load.
- `tests/`: mirrors `app/` (added later).

## 3) I negotiated the data model to keep it very simple
- The AI initially proposed `Pokemon` + `Type` + `Ability` with M:N association tables and denormalized caches.
- I challenged that for a case test and proposed a single table: `pokemon` with `id`, `name`, `pokedex_number`, `height_m`, `weight_kg`, `base_experience`, `stats` (dict), `types` (list[str]), `abilities` (list[str]).
- The AI listed trade-offs across four options (fully denormalized, semi, normalized, hybrid). I decided for the 1-table denormalized approach, trusting PokeAPI as the source of truth. The AI accepted and adapted the code.

## 4) ID policy evolved (Pokedex number → UUID v4)
- At one point, I asked to use Pokédex number as the primary key ID (no autoincrement) and added a `DELETE` endpoint.
- Later, I switched to UUID v4 as the `id` to support future variations/mega evolutions sharing the same `pokedex_number`.
- We updated the model to `id: UUID v4 (string)`, and kept `pokedex_number` as a plain indexed field.

## 5) I enforced consistency in the GET responses
- Initially, `GET /pokemon` returned a summary while `GET /pokemon/<id_or_name>` returned full details.
- I requested full details everywhere. The AI introduced a helper `_to_detail_dict` and made `GET /pokemon` return the same detailed shape. I also asked for a `limit` query param (default 200).

## 6) PokeAPI name issues: I drove the solution to a strict rule + alias map
- I discovered PokeAPI doesn’t always accept lowercase forms (e.g., `mewtwo` vs `MewTwo`, `mrmime` vs `mr-mime`).
- The AI proposed a slug strategy with multiple candidates (raw, lower, slugified) and even an index fetch. I rejected the index approach and tried the slug candidates—but some cases still failed.
- I asked the AI to build a diagnostic script to try ALL names strictly as lowercase (no symbols) up to #1025. It found 76 failures.
- I then defined a product rule: my API will receive names strictly in lowercase with no symbols. For upstream exceptions, we’ll map using a fixed `POKEMON_ALIASES` dict (e.g., `mrmime` → `mr-mime`, `mewtwo` → `MewTwo`, `typenull` → `type-null`, etc.).
- We removed slug code and kept only the alias mapping in the client. From then on, `POST /add-pokemon` worked 100% with the rule + aliases.

## 7) I requested global error handlers and logging middlewares
- I didn’t want try/except inside each endpoint. I asked for centralized error handlers:
  - Pydantic `ValidationError` → 400 with details
  - `PokemonNotFoundError` → 404
  - `PokeAPIError` → 502 (upstream error)
  - `SQLAlchemyError` → 500 with session rollback
  - catch-all `Exception` → 500
- I also asked for request/response logging middlewares (no nesting), registered via `register_middlewares(app)` and called from `main.py`.

## 8) Pre-commit and tests + CI to close the loop
- I added local quality gates (ruff format/lint and pyright type-check) as a pre-commit workflow in my process.
- After the core app was stable, we added tests mirroring the `app/` structure, covering schemas, sanitizer, PokeAPI client (aliases), ingestion service, and routes (including limit and delete).
- Finally, I asked for a GitHub Actions workflow to run `pytest` on every push/PR.

## 9) Final result
- Minimal app, easy to run: `python -m app.main`.
- Single-table model with JSON fields for `stats`, `types`, `abilities` and UUID v4 IDs.
- Input rule enforced for names and an alias map to make PokeAPI calls reliable.
- Consistent full-detail responses across list and detail.
- Centralized error handling and logging middlewares.
- Tests and CI in place.
