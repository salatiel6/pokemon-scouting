from app.main import create_app


def test_env_configuration_overrides(monkeypatch, tmp_path) -> None:
    """
    Ensure environment variables (or .env) override default configuration.

    :param monkeypatch: pytest monkeypatch fixture
    :param tmp_path: temporary directory provided by pytest

    :return: None
    :raises: None
    """
    db_path = tmp_path / "envtest.db"

    # Set environment variables to override defaults
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", f"sqlite:///{db_path}")
    monkeypatch.setenv("POKEAPI_BASE_URL", "https://example.com/api/v2")
    monkeypatch.setenv("SYNC_ON_START", "false")
    monkeypatch.setenv("CACHE_TYPE", "NullCache")
    monkeypatch.setenv("CACHE_DEFAULT_TIMEOUT", "42")
    monkeypatch.setenv("STALE_TTL_MINUTES", "7")
    monkeypatch.setenv("DISABLE_BACKGROUND_SYNC", "true")
    monkeypatch.setenv("SYNC_INTERVAL_MINUTES", "13")
    monkeypatch.setenv("REFRESH_BATCH_SIZE", "5")

    app = create_app()
    # No need to run server; just verify config values
    assert app.config["SQLALCHEMY_DATABASE_URI"] == f"sqlite:///{db_path}"
    assert app.config["POKEAPI_BASE_URL"] == "https://example.com/api/v2"
    assert app.config["SYNC_ON_START"] is False
    assert app.config["CACHE_TYPE"] == "NullCache"
    assert app.config["CACHE_DEFAULT_TIMEOUT"] == 42
    assert app.config["STALE_TTL_MINUTES"] == 7
    assert app.config["DISABLE_BACKGROUND_SYNC"] is True
    assert app.config["SYNC_INTERVAL_MINUTES"] == 13
    assert app.config["REFRESH_BATCH_SIZE"] == 5
