"""Tests for Superset hooks configuration."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from phlo_superset import hooks


def test_superset_auth_provider_defaults(monkeypatch) -> None:
    """Login provider should default cleanly when unset."""
    monkeypatch.delenv("SUPERSET_AUTH_PROVIDER", raising=False)

    assert hooks._superset_auth_provider() == "db"


def test_superset_database_name_is_configurable(monkeypatch) -> None:
    """Displayed database name should come from configuration when set."""
    monkeypatch.setenv("SUPERSET_DATABASE_NAME", "analytics")

    assert hooks._superset_database_name() == "analytics"


def test_superset_database_name_uses_query_engine_metadata(monkeypatch) -> None:
    """Database name should fall back to query-engine catalog metadata."""
    monkeypatch.delenv("SUPERSET_DATABASE_NAME", raising=False)
    monkeypatch.delenv("SUPERSET_QUERY_ENGINE", raising=False)
    monkeypatch.setattr(hooks, "discover_capabilities", lambda: None)
    monkeypatch.setattr(
        hooks,
        "resolve_capability",
        lambda kind, name=None: type(
            "Resolution", (), {"metadata": {"default_catalog": "iceberg"}}
        )(),
    )

    assert hooks._superset_database_name() == "iceberg"


def test_superset_database_uri_prefers_explicit_config(monkeypatch) -> None:
    """Explicit SQLAlchemy URI should bypass capability discovery."""
    monkeypatch.setenv("SUPERSET_DATABASE_URI", "duckdb:///warehouse.duckdb")

    assert hooks._configured_database_uri() == "duckdb:///warehouse.duckdb"


def test_superset_database_uri_can_be_derived_from_query_engine_metadata(monkeypatch) -> None:
    """Capability metadata should provide a query-engine-neutral database URI."""
    monkeypatch.delenv("SUPERSET_DATABASE_URI", raising=False)
    monkeypatch.setattr(hooks, "discover_capabilities", lambda: None)
    monkeypatch.setattr(
        hooks,
        "resolve_capability",
        lambda capability, name=None: SimpleNamespace(
            metadata={
                "sqlalchemy_uri_template": "trino://{host}:{port}/{default_catalog}",
                "host": "trino",
                "port": 8080,
                "default_catalog": "analytics",
            }
        ),
    )

    assert hooks._discover_query_engine_database_uri() == "trino://trino:8080/analytics"


def test_superset_database_uri_fails_without_config_or_metadata(monkeypatch) -> None:
    """Superset setup should fail clearly when no neutral database URI can be resolved."""
    monkeypatch.delenv("SUPERSET_DATABASE_URI", raising=False)
    monkeypatch.setattr(hooks, "discover_capabilities", lambda: None)
    monkeypatch.setattr(hooks, "resolve_capability", lambda capability, name=None: None)

    with pytest.raises(RuntimeError, match="SUPERSET_DATABASE_URI"):
        hooks._discover_query_engine_database_uri()
