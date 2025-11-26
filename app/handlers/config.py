from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application settings loaded from environment variables (.env).

    All variables are REQUIRED (no defaults). If any is missing, a validation
    error will be raised at access time when the singleton is first created.

    :return: None
    :raises: pydantic.ValidationError if any env var is missing/invalid
    """

    # Database
    SQLALCHEMY_DATABASE_URI: str

    # Upstream API
    POKEAPI_BASE_URL: str

    # Seed/load and background behavior
    SYNC_ON_START: bool
    DISABLE_BACKGROUND_SYNC: bool
    SYNC_INTERVAL_MINUTES: int
    STALE_TTL_MINUTES: int
    REFRESH_BATCH_SIZE: int

    # Cache
    CACHE_TYPE: str
    CACHE_DEFAULT_TIMEOUT: int

    # Load from .env file at project root by default
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Public proxy; importers can `from app.handlers.config import settings`
settings = Settings()  # type: ignore
