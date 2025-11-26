from typing import Any

from flask import Flask
from flask_caching import Cache

from app.handlers.logger import logger

# Global cache instance (Flask-Caching)
cache = Cache()


def init_cache(app: Flask) -> None:
    """
    Initialize Flask-Caching on the given app instance.

    Uses SimpleCache by default with a sensible timeout. Configuration can be
    customized via Flask app.config:
      - CACHE_TYPE (default: "SimpleCache")
      - CACHE_DEFAULT_TIMEOUT (default: 1800 seconds)

    :param app: Flask application instance

    :return: None
    """
    # Provide defaults if not set
    app.config.setdefault("CACHE_TYPE", "SimpleCache")
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", 1800)  # 30 minutes

    cache.init_app(app)
    logger.info(
        f"Cache initialized "
        f"(type={app.config["CACHE_TYPE"]}, default_timeout={app.config["CACHE_DEFAULT_TIMEOUT"]})"
    )


def cache_get(key: str) -> Any:
    """
    Safe cache getter with debug logging.

    :param key: cache key

    :return: cached value or None
    """
    try:
        val = cache.get(key)
    except Exception as e:
        # Cache likely not initialized in this context (e.g., tests). Treat as miss.
        logger.error(f"cache error: {e}")
        logger.debug(f"cache unavailable, treating as miss: {key}")
        return None
    if val is None:
        logger.debug(f"cache miss: {key}")
    else:
        logger.debug(f"cache hit: {key}")
    return val


def cache_set(key: str, value: Any, timeout: int | None = None) -> None:
    """
    Safe cache setter with debug logging.

    :param key: cache key
    :param value: value to store
    :param timeout: optional TTL in seconds (falls back to CACHE_DEFAULT_TIMEOUT)

    :return: None
    """
    try:
        cache.set(key, value, timeout=timeout)
        logger.debug(f"cache set: {key} (timeout={timeout})")
    except Exception as e:
        # Cache not initialized
        logger.error(f"cache error: {e}")
        logger.debug(f"cache not initialized; skip set: {key}")
