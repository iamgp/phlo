"""Tests for OpenMetadata capability resolution helpers."""

from unittest.mock import Mock, patch

from phlo_openmetadata.capabilities import resolve_catalog_scanner, resolve_query_engine_catalog


def test_resolve_catalog_scanner_returns_provider():
    """Capability helper returns the resolved scanner provider."""
    provider = Mock()

    with (
        patch("phlo_openmetadata.capabilities._discover_capabilities"),
        patch(
            "phlo_openmetadata.capabilities.resolve_capability",
            return_value=Mock(provider=provider),
        ) as resolve_mock,
    ):
        result = resolve_catalog_scanner("nessie")

    assert result is provider
    resolve_mock.assert_called_once_with("catalog_scanner", "nessie")


def test_resolve_catalog_scanner_raises_when_missing():
    """Capability helper fails clearly when scanner capability is unavailable."""
    with (
        patch("phlo_openmetadata.capabilities._discover_capabilities"),
        patch("phlo_openmetadata.capabilities.resolve_capability", return_value=None),
    ):
        try:
            resolve_catalog_scanner("nessie")
        except RuntimeError as exc:
            assert "nessie" in str(exc)
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected RuntimeError")


def test_resolve_query_engine_catalog_uses_capability_metadata():
    """Catalog helper reads stable metadata instead of provider internals."""
    with (
        patch("phlo_openmetadata.capabilities._discover_capabilities"),
        patch(
            "phlo_openmetadata.capabilities.resolve_capability",
            return_value=Mock(metadata={"catalog": "iceberg_dev"}),
        ) as resolve_mock,
    ):
        result = resolve_query_engine_catalog("duckdb", default="fallback")

    assert result == "iceberg_dev"
    resolve_mock.assert_called_once_with("query_engine", "duckdb")


def test_resolve_query_engine_catalog_falls_back_when_metadata_missing():
    """Catalog helper returns the configured fallback when metadata is absent."""
    with (
        patch("phlo_openmetadata.capabilities._discover_capabilities"),
        patch(
            "phlo_openmetadata.capabilities.resolve_capability",
            return_value=Mock(metadata={}),
        ),
    ):
        assert resolve_query_engine_catalog(default="fallback") == "fallback"
