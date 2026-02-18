"""Tests for Nessie settings environment alias resolution."""

from phlo_nessie.settings import get_settings


def test_nessie_default_ref_uses_legacy_iceberg_env(monkeypatch) -> None:
    """Ensure Nessie default ref honors legacy Iceberg reference env var."""
    monkeypatch.delenv("NESSIE_DEFAULT_REF", raising=False)
    monkeypatch.delenv("PHLO_NESSIE_DEFAULT_REF", raising=False)
    monkeypatch.delenv("PHLO_DEFAULT_REF", raising=False)
    monkeypatch.setenv("ICEBERG_NESSIE_REF", "dev")
    get_settings.cache_clear()
    try:
        assert get_settings().nessie_default_ref == "dev"
    finally:
        get_settings.cache_clear()


def test_nessie_default_ref_prefers_nessie_specific_env(monkeypatch) -> None:
    """Ensure Nessie-specific env var takes precedence over legacy fallback."""
    monkeypatch.setenv("NESSIE_DEFAULT_REF", "release")
    monkeypatch.setenv("ICEBERG_NESSIE_REF", "dev")
    get_settings.cache_clear()
    try:
        assert get_settings().nessie_default_ref == "release"
    finally:
        get_settings.cache_clear()
