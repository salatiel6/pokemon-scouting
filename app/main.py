from flask import Flask

from app.api.health import health_bp
from app.api.pokemon import pokemon_bp
from app.db import init_db
from app.handlers.cache import init_cache
from app.handlers.config import settings
from app.handlers.errors import register_error_handlers
from app.handlers.logger import logger
from app.handlers.middlewares import register_middlewares
from app.handlers.scheduler import start_scheduler


def sync_on_start(app_: Flask) -> None:
    """
    Synchronize initial Pokemon data on application startup.

    Reads the seed CSV and uses the existing ingestion flow to upsert entries.
    This function must never crash the application startup; any error is
    logged as a warning and the boot proceeds normally.

    :param app_: A Flask application instance

    :return: None
    """
    try:
        # Use settings to decide whether to run startup sync
        enabled = bool(settings.SYNC_ON_START)
        if not enabled:
            logger.info("SYNC_ON_START is disabled; skipping initial sync.")
            return

        # Lazy imports to avoid circular dependencies and only load when needed
        from app.db.config import read_pokemon_csv
        from app.handlers.ingest_service import IngestService

        with app_.app_context():
            names = read_pokemon_csv()
            if not names:
                logger.info("No seed CSV entries found; skipping initial sync.")
                return
            logger.info(f"Starting initial sync for {len(names)} Pokemon from CSV...")
            service = IngestService()
            result = service.ingest_many(names)
            ok = len(result.get("ok", []))
            not_found = len(result.get("not_found", []))
            errors = len(result.get("errors", []))
            logger.info(f"Initial sync done. ok={ok} not_found={not_found} errors={errors}")
    except Exception as e:  # pragma: no cover - safety net for startup
        logger.warning(f"Initial sync failed (boot continues): {e}")


def create_app() -> Flask:
    """
    Create and configure the Flask application instance.

    :return: A configured Flask app_ instance
    :raises: None
    """
    app_ = Flask(__name__)

    # Reflect settings into app.config so existing components continue to work
    app_.config["SQLALCHEMY_DATABASE_URI"] = settings.SQLALCHEMY_DATABASE_URI
    app_.config["POKEAPI_BASE_URL"] = settings.POKEAPI_BASE_URL
    app_.config["SYNC_ON_START"] = settings.SYNC_ON_START
    app_.config["CACHE_TYPE"] = settings.CACHE_TYPE
    app_.config["CACHE_DEFAULT_TIMEOUT"] = settings.CACHE_DEFAULT_TIMEOUT
    app_.config["STALE_TTL_MINUTES"] = settings.STALE_TTL_MINUTES
    app_.config["DISABLE_BACKGROUND_SYNC"] = settings.DISABLE_BACKGROUND_SYNC
    app_.config["SYNC_INTERVAL_MINUTES"] = settings.SYNC_INTERVAL_MINUTES
    app_.config["REFRESH_BATCH_SIZE"] = settings.REFRESH_BATCH_SIZE

    # Initialize database, middlewares, and register HTTP routes
    init_db(app_)
    # Initialize caching layer
    init_cache(app_)
    # Perform initial CSV sync (non-fatal on errors)
    sync_on_start(app_)
    register_middlewares(app_)
    # Register blueprints (API routes)
    app_.register_blueprint(pokemon_bp)
    app_.register_blueprint(health_bp)
    register_error_handlers(app_)

    # Start background scheduler
    if not settings.DISABLE_BACKGROUND_SYNC:
        start_scheduler(app_)
    else:
        logger.info("Background sync is disabled via configuration.")

    return app_


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
