"""Tests for Sling replication decorator."""

import pytest
from types import SimpleNamespace

from phlo.exceptions import PhloConfigError
from phlo_sling.decorator import (
    _validate_incremental_config,
    _validate_replication_mode,
    clear_sling_assets,
    get_sling_assets,
    phlo_sling_replication,
)


def test_validate_replication_mode_valid():
    """Valid modes do not raise."""
    for mode in ("full-refresh", "incremental", "snapshot", "backfill"):
        _validate_replication_mode(mode)


def test_validate_replication_mode_invalid():
    """Invalid mode raises PhloConfigError."""
    with pytest.raises(PhloConfigError):
        _validate_replication_mode("upsert")


def test_validate_incremental_requires_update_key():
    """Incremental mode without update_key raises."""
    with pytest.raises(PhloConfigError):
        _validate_incremental_config("incremental", None)


def test_validate_incremental_with_update_key():
    """Incremental mode with update_key does not raise."""
    _validate_incremental_config("incremental", "updated_at")


def test_decorator_registers_asset():
    """Decorator registers an asset in the global registry."""
    clear_sling_assets()

    @phlo_sling_replication(
        stream_name="public.users",
        table_name="users",
        source_conn="TEST_PG",
        group="test",
        mode="full-refresh",
    )
    def my_replication(context):
        return None

    assets = get_sling_assets()
    assert len(assets) == 1
    assert assets[0].key == "sling_users"
    assert assets[0].group == "test"
    assert "sling" in assets[0].kinds
    clear_sling_assets()


def test_decorator_attaches_config():
    """Decorator attaches _phlo_replication_config to the function."""
    clear_sling_assets()

    @phlo_sling_replication(
        stream_name="public.orders",
        table_name="orders",
        source_conn="TEST_PG",
        group="test",
        mode="full-refresh",
        primary_key="id",
    )
    def my_replication(context):
        return None

    assert hasattr(my_replication, "_phlo_replication_config")
    config = my_replication._phlo_replication_config  # type: ignore[attr-defined]
    assert config.stream_name == "public.orders"  # type: ignore[attr-defined]
    assert config.primary_key == ["id"]  # type: ignore[attr-defined]
    clear_sling_assets()


def test_decorator_uses_configured_default_mode(monkeypatch) -> None:
    """Decorator should honor SLING_DEFAULT_MODE when mode is omitted."""
    clear_sling_assets()
    monkeypatch.setattr(
        "phlo_sling.decorator.get_settings",
        lambda: SimpleNamespace(sling_default_mode="full-refresh"),
    )

    @phlo_sling_replication(
        stream_name="public.users",
        table_name="users",
        source_conn="TEST_PG",
        group="test",
    )
    def my_replication(context):
        return None

    config = my_replication._phlo_replication_config  # type: ignore[attr-defined]
    assert config.mode == "full-refresh"  # type: ignore[attr-defined]
    clear_sling_assets()
