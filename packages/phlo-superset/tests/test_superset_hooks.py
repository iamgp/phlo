"""Tests for Superset hooks configuration."""

from __future__ import annotations

from phlo_superset import hooks


def test_superset_auth_provider_defaults(monkeypatch) -> None:
    """Login provider should default cleanly when unset."""
    monkeypatch.delenv("SUPERSET_AUTH_PROVIDER", raising=False)

    assert hooks._superset_auth_provider() == "db"


def test_superset_database_name_is_configurable(monkeypatch) -> None:
    """Displayed database name should come from configuration when set."""
    monkeypatch.setenv("SUPERSET_DATABASE_NAME", "analytics")

    assert hooks._superset_database_name() == "analytics"
