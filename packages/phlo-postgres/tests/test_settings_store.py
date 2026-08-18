"""Tests for the PostgreSQL settings store capability registration."""

from __future__ import annotations

from unittest.mock import patch

from phlo.capabilities import SettingsStoreSpec
from phlo.plugins.observatory_settings import SettingsService, SettingsStore
from phlo_postgres.plugin import PostgresResourceProvider
from phlo_postgres.settings_store import PostgresSettingsStore, get_settings_stores


def test_postgres_settings_store_is_settings_service() -> None:
    """PostgresSettingsStore must extend SettingsService for DSN-based storage."""
    with patch("phlo_postgres.settings_store.get_postgres_settings") as mock:
        mock.return_value.get_postgres_connection_string.return_value = (
            "postgresql://phlo:phlo@localhost:5432/phlo"
        )
        store = PostgresSettingsStore()
    assert isinstance(store, SettingsService)
    assert store._db_url == "postgresql://phlo:phlo@localhost:5432/phlo"


def test_postgres_settings_store_implements_settings_store_protocol() -> None:
    with patch("phlo_postgres.settings_store.get_postgres_settings") as mock:
        mock.return_value.get_postgres_connection_string.return_value = (
            "postgresql://phlo:phlo@localhost:5432/phlo"
        )
        store = PostgresSettingsStore()
    assert isinstance(store, SettingsStore)


def test_get_settings_stores_returns_capability_spec() -> None:
    with patch("phlo_postgres.settings_store.get_postgres_settings") as mock:
        mock.return_value.get_postgres_connection_string.return_value = (
            "postgresql://phlo:phlo@localhost:5432/phlo"
        )
        specs = get_settings_stores()
    assert len(specs) == 1
    assert isinstance(specs[0], SettingsStoreSpec)
    assert specs[0].name == "postgres"
    assert isinstance(specs[0].provider, PostgresSettingsStore)


def test_postgres_resource_provider_exposes_settings_store() -> None:
    """PostgresResourceProvider must expose get_settings_stores for discovery."""
    with patch("phlo_postgres.settings_store.get_postgres_settings") as mock:
        mock.return_value.get_postgres_connection_string.return_value = (
            "postgresql://phlo:phlo@localhost:5432/phlo"
        )
        provider = PostgresResourceProvider()
        specs = provider.get_settings_stores()
    assert len(specs) == 1
    assert specs[0].name == "postgres"
    assert isinstance(specs[0].provider, SettingsStore)
