"""Tests for durable Observatory settings storage and fail-closed behaviour.

Covers the acceptance criteria from issue #626:
- Core settings code has no provider-package import.
- Durable backend selected by default; memory only via explicit config.
- PostgreSQL unavailable → 503 (StorageUnavailableError); no in-memory record.
- Same-process recovery after the database returns.
- Invalid backend names fail configuration validation.
- Error responses and logs contain no DSN or password.
- Global and extension settings use the same durable capability.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from phlo.plugins.observatory_settings import (
    InMemorySettingsService,
    ObservatorySettingsStorageConfig,
    SettingsScope,
    SettingsService,
    SettingsStore,
    StorageUnavailableError,
    _reset_memory_service,
    get_settings_service,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clear_settings_store_capability() -> None:
    from phlo.capabilities import clear_capabilities

    clear_capabilities("settings_store")


def _register_mock_settings_store(store) -> None:
    from phlo.capabilities import SettingsStoreSpec, register_capability

    register_capability("settings_store", SettingsStoreSpec(name="postgres", provider=store))


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    """Ensure each test starts with a clean capability registry and memory cache."""
    _clear_settings_store_capability()
    _reset_memory_service()
    # Default to postgres backend unless a test overrides it.
    monkeypatch.setenv("PHLO_OBSERVATORY_SETTINGS_BACKEND", "postgres")
    monkeypatch.delenv("PHLO_OBSERVATORY_SETTINGS_DB_URL", raising=False)
    yield
    _clear_settings_store_capability()
    _reset_memory_service()


# ---------------------------------------------------------------------------
# Import boundary
# ---------------------------------------------------------------------------


def test_core_observatory_settings_does_not_import_phlo_postgres() -> None:
    """Core settings module must not import any provider package."""
    module_path = Path(importlib.import_module("phlo.plugins.observatory_settings").__file__)
    tree = ast.parse(module_path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("phlo_postgres"), (
                    f"core imports provider package: {alias.name}"
                )
        elif isinstance(node, ast.ImportFrom):
            assert node.module is None or not node.module.startswith("phlo_postgres"), (
                f"core imports provider package: {node.module}"
            )


# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------


def test_default_backend_is_postgres() -> None:
    config = ObservatorySettingsStorageConfig()
    assert config.observatory_settings_backend == "postgres"


def test_memory_backend_via_explicit_config(monkeypatch) -> None:
    monkeypatch.setenv("PHLO_OBSERVATORY_SETTINGS_BACKEND", "memory")
    config = ObservatorySettingsStorageConfig()
    assert config.observatory_settings_backend == "memory"


def test_invalid_backend_name_fails_validation(monkeypatch) -> None:
    monkeypatch.setenv("PHLO_OBSERVATORY_SETTINGS_BACKEND", "redis")
    with pytest.raises(Exception, match="postgres|memory"):
        ObservatorySettingsStorageConfig()


# ---------------------------------------------------------------------------
# Memory mode
# ---------------------------------------------------------------------------


def test_memory_mode_returns_in_memory_service(monkeypatch) -> None:
    monkeypatch.setenv("PHLO_OBSERVATORY_SETTINGS_BACKEND", "memory")
    service = get_settings_service()
    assert isinstance(service, InMemorySettingsService)


def test_memory_mode_persists_across_calls(monkeypatch) -> None:
    monkeypatch.setenv("PHLO_OBSERVATORY_SETTINGS_BACKEND", "memory")
    service1 = get_settings_service()
    service1.put(SettingsScope.GLOBAL, "test", {"v": 1})
    service2 = get_settings_service()
    assert service2 is service1
    record = service2.get(SettingsScope.GLOBAL, "test")
    assert record is not None
    assert record.settings == {"v": 1}


# ---------------------------------------------------------------------------
# Postgres mode — capability resolution
# ---------------------------------------------------------------------------


def test_postgres_mode_resolves_capability() -> None:
    mock_store = MagicMock(spec=SettingsStore)
    _register_mock_settings_store(mock_store)
    service = get_settings_service()
    assert service is mock_store


def test_postgres_mode_without_capability_raises_storage_unavailable() -> None:
    with pytest.raises(StorageUnavailableError, match="not available"):
        get_settings_service()


def test_postgres_mode_does_not_create_in_memory_record_on_failure() -> None:
    """When the durable backend is unavailable, no in-memory write occurs."""
    with pytest.raises(StorageUnavailableError):
        get_settings_service()
    # The memory singleton must not have been populated.
    from phlo.plugins.observatory_settings import _memory_service

    assert _memory_service is None


# ---------------------------------------------------------------------------
# Postgres mode — connection failure and recovery
# ---------------------------------------------------------------------------


def test_connection_failure_raises_storage_unavailable() -> None:
    """A psycopg2 connection failure must surface as StorageUnavailableError."""
    store = SettingsService("postgresql://invalid:5432/phlo")
    _register_mock_settings_store(store)

    with (
        patch("psycopg2.connect", side_effect=OSError("connection refused")),
        pytest.raises(StorageUnavailableError, match="Settings storage is unavailable"),
    ):
        store.get(SettingsScope.GLOBAL, "observatory")


def test_recovery_after_database_becomes_available() -> None:
    """First call fails, second call succeeds in the same process."""
    store = SettingsService("postgresql://localhost:5432/phlo")
    _register_mock_settings_store(store)

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ({"version": 1}, None)
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = False

    call_count = {"n": 0}

    def fake_connect(*_args, **_kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise OSError("connection refused")
        return mock_conn

    with patch("psycopg2.connect", side_effect=fake_connect):
        # First call — database unavailable.
        with pytest.raises(StorageUnavailableError):
            store.get(SettingsScope.GLOBAL, "observatory")

        # Second call — same process, no cache clear — succeeds.
        record = store.get(SettingsScope.GLOBAL, "observatory")
        assert record is not None
        assert record.settings == {"version": 1}


def test_get_settings_service_retries_capability_resolution_after_failure() -> None:
    """get_settings_service() must not cache a failure; later calls retry."""
    # No capability registered → first call fails.
    with pytest.raises(StorageUnavailableError):
        get_settings_service()

    # Register capability → second call succeeds without cache clear.
    mock_store = MagicMock(spec=SettingsStore)
    _register_mock_settings_store(mock_store)
    service = get_settings_service()
    assert service is mock_store


# ---------------------------------------------------------------------------
# DSN safety
# ---------------------------------------------------------------------------


def test_storage_unavailable_error_contains_no_dsn() -> None:
    store = SettingsService("postgresql://user:secret@host:5432/db")
    _register_mock_settings_store(store)

    with patch("psycopg2.connect", side_effect=OSError("connection refused")):
        try:
            store.get(SettingsScope.GLOBAL, "observatory")
            pytest.fail("expected StorageUnavailableError")
        except StorageUnavailableError as exc:
            msg = str(exc)
            assert "user:secret" not in msg
            assert "postgresql://" not in msg
            assert "host:5432" not in msg


def test_get_settings_service_error_contains_no_dsn(monkeypatch) -> None:
    monkeypatch.setenv("PHLO_OBSERVATORY_SETTINGS_DB_URL", "postgresql://user:secret@host:5432/db")
    store = get_settings_service()
    assert isinstance(store, SettingsService)

    with patch("psycopg2.connect", side_effect=OSError("connection refused")):
        try:
            store.get(SettingsScope.GLOBAL, "observatory")
            pytest.fail("expected StorageUnavailableError")
        except StorageUnavailableError as exc:
            msg = str(exc)
            assert "user:secret" not in msg
            assert "postgresql://" not in msg


# ---------------------------------------------------------------------------
# Global and extension settings use the same capability
# ---------------------------------------------------------------------------


def test_global_and_extension_use_same_capability() -> None:
    """Both scopes resolve the same settings_store capability."""
    mock_store = MagicMock(spec=SettingsStore)
    mock_store.get.return_value = None
    _register_mock_settings_store(mock_store)

    service = get_settings_service()
    service.get(SettingsScope.GLOBAL, "observatory.core")
    service.get(SettingsScope.EXTENSION, "observatory.extension.demo")

    # Same provider instance for both scopes.
    assert mock_store.get.call_count == 2
    mock_store.get.assert_any_call(SettingsScope.GLOBAL, "observatory.core")
    mock_store.get.assert_any_call(SettingsScope.EXTENSION, "observatory.extension.demo")


# ---------------------------------------------------------------------------
# DSN override
# ---------------------------------------------------------------------------


def test_explicit_dsn_override_bypasses_capability(monkeypatch) -> None:
    monkeypatch.setenv("PHLO_OBSERVATORY_SETTINGS_DB_URL", "postgresql://override:5432/phlo")
    service = get_settings_service()
    assert isinstance(service, SettingsService)
    assert service._db_url == "postgresql://override:5432/phlo"
