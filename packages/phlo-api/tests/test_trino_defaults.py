"""Tests for capability-driven Trino API defaults."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from phlo_api.observatory_api import trino


def test_resolve_default_catalog_uses_query_engine_metadata(monkeypatch) -> None:
    """Catalog resolution should prefer query-engine capability metadata."""
    monkeypatch.delenv("PHLO_QUERY_CATALOG", raising=False)
    monkeypatch.delenv("TRINO_CATALOG", raising=False)

    with (
        patch("phlo_api.observatory_api.trino.discover_capabilities"),
        patch(
            "phlo_api.observatory_api.trino.resolve_capability",
            return_value=Mock(metadata={"default_catalog": "warehouse"}),
        ),
    ):
        assert trino.resolve_default_catalog() == "warehouse"


def test_resolve_default_catalog_requires_configuration(monkeypatch) -> None:
    """Catalog resolution should fail clearly when nothing provides a default."""
    monkeypatch.delenv("PHLO_QUERY_CATALOG", raising=False)
    monkeypatch.delenv("TRINO_CATALOG", raising=False)

    with (
        patch("phlo_api.observatory_api.trino.discover_capabilities"),
        patch("phlo_api.observatory_api.trino.resolve_capability", return_value=None),
    ):
        with pytest.raises(RuntimeError, match="No default query catalog"):
            trino.resolve_default_catalog()


def test_resolve_default_ref_uses_query_engine_metadata(monkeypatch) -> None:
    """Ref resolution should prefer query-engine capability metadata."""
    monkeypatch.delenv("PHLO_DEFAULT_REF", raising=False)
    monkeypatch.delenv("NESSIE_DEFAULT_REF", raising=False)

    with (
        patch("phlo_api.observatory_api.trino.discover_capabilities"),
        patch(
            "phlo_api.observatory_api.trino.resolve_capability",
            return_value=Mock(metadata={"default_ref": "dev"}),
        ),
    ):
        assert trino.resolve_default_ref() == "dev"
