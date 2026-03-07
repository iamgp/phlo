"""Tests for Hasura API backend capability registration."""

from __future__ import annotations

from phlo_hasura.resource_provider import HasuraResourceProvider


def test_hasura_resource_provider_exposes_api_backend() -> None:
    """Hasura should register a swappable API backend capability."""
    provider = HasuraResourceProvider()

    specs = provider.get_api_backends()

    assert [spec.name for spec in specs] == ["hasura"]
    assert specs[0].metadata["backend_kind"] == "graphql"
    assert hasattr(specs[0].provider, "health_check")
    assert hasattr(specs[0].provider, "describe")
