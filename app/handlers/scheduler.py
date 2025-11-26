from datetime import UTC, datetime, timedelta
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from sqlalchemy import or_

from app.handlers.config import settings
from app.handlers.ingest_service import IngestService
from app.handlers.logger import logger
from app.models.pokemon import Pokemon


def _select_stale_names(app: Flask) -> List[str]:
    """
    Select a batch of stale (or never refreshed) Pokemon names for refreshing.

    :param app: Flask application instance (for app context/config)

    :return: List of Pokemon canonical names to refresh
    """
    with app.app_context():
        minutes = int(settings.STALE_TTL_MINUTES)
        batch = int(settings.REFRESH_BATCH_SIZE)
        threshold = datetime.now(UTC) - timedelta(minutes=minutes)
        q = (
            Pokemon.query.filter(or_(Pokemon.refreshed_at.is_(None), Pokemon.refreshed_at < threshold))
            .order_by(Pokemon.refreshed_at.is_(None).desc(), Pokemon.refreshed_at.asc())
            .limit(batch)
        )
        names = [p.name for p in q.all()]
        return names


def refresh_stale_job(app: Flask) -> None:
    """
    Background job: refresh a batch of stale Pokemon from PokeAPI using the
    existing ingestion flow (DB-first + cache-first implemented there).

    :param app: Flask application instance

    :return: None
    """
    try:
        names = _select_stale_names(app)
        if not names:
            logger.debug("scheduler: no stale Pokemon to refresh")
            return
        logger.info(f"scheduler: refreshing {len(names)} stale Pokemon...")
        with app.app_context():
            service = IngestService()
            result = service.ingest_many(names)
            logger.info(
                "scheduler: refresh done ok=%s not_found=%s errors=%s",
                len(result.get("ok", [])),
                len(result.get("not_found", [])),
                len(result.get("errors", [])),
            )
    except Exception as e:  # pragma: no cover - defensive logging only
        logger.error(f"scheduler error: {e}")


def start_scheduler(app: Flask) -> None:
    """
    Start a BackgroundScheduler that periodically refreshes stale Pokemon.

    The scheduler is stored in app.extensions['apscheduler'] to prevent
    multiple instances during development reloads.

    :param app: Flask application instance

    :return: None
    """
    if settings.DISABLE_BACKGROUND_SYNC:
        logger.info("scheduler: background sync disabled by configuration")
        return

    # Avoid duplicate starters (e.g., in dev reloads)
    if hasattr(app, "extensions") and app.extensions.get("apscheduler") is not None:
        logger.info("scheduler: already started, skipping")
        return

    scheduler = BackgroundScheduler(daemon=True)
    interval = int(settings.SYNC_INTERVAL_MINUTES)
    scheduler.add_job(
        func=refresh_stale_job,
        trigger="interval",
        minutes=interval,
        args=[app],
        id="refresh_stale_pokemon",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    if not hasattr(app, "extensions"):
        app.extensions = {}
    app.extensions["apscheduler"] = scheduler
    logger.info(f"scheduler: started (interval={interval}m)")
