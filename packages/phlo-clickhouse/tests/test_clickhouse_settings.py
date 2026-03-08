"""Tests for ClickHouse settings."""

from phlo_clickhouse.settings import ClickHouseSettings, get_settings


def test_clickhouse_settings_defaults():
    """Validate ClickHouse settings default values."""

    settings = ClickHouseSettings()

    assert settings.clickhouse_host == "clickhouse"
    assert settings.clickhouse_http_port == 8123
    assert settings.clickhouse_native_port == 19000
    assert settings.clickhouse_user == "default"
    assert settings.clickhouse_password == ""
    assert settings.clickhouse_db == "default"
    assert settings.clickhouse_secure is False


def test_clickhouse_settings_http_endpoint():
    """Validate ClickHouse HTTP endpoint generation."""

    settings = ClickHouseSettings()

    assert settings.clickhouse_http_endpoint() == "clickhouse:8123"


def test_clickhouse_settings_native_endpoint():
    """Validate ClickHouse native endpoint generation."""

    settings = ClickHouseSettings()

    assert settings.clickhouse_native_endpoint() == "clickhouse:19000"


def test_clickhouse_settings_with_overrides():
    """Validate ClickHouse settings with override values."""

    settings = ClickHouseSettings(
        clickhouse_host="my-host",
        clickhouse_http_port=9000,
        clickhouse_native_port=9001,
        clickhouse_user="admin",
        clickhouse_password="secret",
        clickhouse_db="mydb",
        clickhouse_secure=True,
    )

    assert settings.clickhouse_host == "my-host"
    assert settings.clickhouse_http_port == 9000
    assert settings.clickhouse_native_port == 9001
    assert settings.clickhouse_user == "admin"
    assert settings.clickhouse_password == "secret"
    assert settings.clickhouse_db == "mydb"
    assert settings.clickhouse_secure is True


def test_get_settings_returns_cached():
    """Validate that get_settings returns cached instance."""

    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2
