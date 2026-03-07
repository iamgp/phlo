"""Tests for OpenMetadata capability resolution helpers."""

from unittest.mock import Mock, patch

from phlo_openmetadata.capabilities import resolve_catalog_scanner


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
