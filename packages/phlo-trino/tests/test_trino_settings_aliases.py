"""Tests for Trino settings environment alias resolution."""

from phlo_trino.settings import get_settings


def test_trino_default_ref_uses_legacy_iceberg_env(monkeypatch) -> None:
    """Ensure Trino default ref honors legacy Iceberg reference env var."""
    monkeypatch.delenv("TRINO_DEFAULT_REF", raising=False)
    monkeypatch.delenv("PHLO_TRINO_DEFAULT_REF", raising=False)
    monkeypatch.delenv("PHLO_DEFAULT_REF", raising=False)
    monkeypatch.setenv("ICEBERG_NESSIE_REF", "dev")
    get_settings.cache_clear()
    try:
        assert get_settings().trino_default_ref == "dev"
    finally:
        get_settings.cache_clear()


def test_trino_default_ref_prefers_trino_specific_env(monkeypatch) -> None:
    """Ensure Trino-specific env var takes precedence over legacy fallback."""
    monkeypatch.setenv("TRINO_DEFAULT_REF", "release")
    monkeypatch.setenv("ICEBERG_NESSIE_REF", "dev")
    get_settings.cache_clear()
    try:
        assert get_settings().trino_default_ref == "release"
    finally:
        get_settings.cache_clear()
