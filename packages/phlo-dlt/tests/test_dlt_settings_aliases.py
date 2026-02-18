"""Tests for DLT settings environment alias resolution."""

from phlo_dlt.registry import TableConfig
from phlo_dlt.settings import get_settings


def test_dlt_namespace_uses_legacy_iceberg_env(monkeypatch) -> None:
    """Ensure DLT still honors legacy Iceberg namespace configuration."""
    monkeypatch.delenv("DLT_DEFAULT_NAMESPACE", raising=False)
    monkeypatch.delenv("PHLO_DLT_DEFAULT_NAMESPACE", raising=False)
    monkeypatch.setenv("ICEBERG_DEFAULT_NAMESPACE", "bronze")
    get_settings.cache_clear()
    try:
        assert get_settings().dlt_default_namespace == "bronze"
        table = TableConfig(
            table_name="events",
            iceberg_schema=object(),
            validation_schema=None,
            unique_key="id",
            group_name="ingestion",
        )
        assert table.full_table_name == "bronze.events"
    finally:
        get_settings.cache_clear()


def test_dlt_namespace_prefers_dlt_specific_env(monkeypatch) -> None:
    """Ensure DLT-specific setting overrides legacy fallback setting."""
    monkeypatch.setenv("DLT_DEFAULT_NAMESPACE", "raw_dlt")
    monkeypatch.setenv("ICEBERG_DEFAULT_NAMESPACE", "bronze")
    get_settings.cache_clear()
    try:
        assert get_settings().dlt_default_namespace == "raw_dlt"
    finally:
        get_settings.cache_clear()
