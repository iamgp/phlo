"""Tests for service plugin example."""

from phlo_example.service import ExampleCacheServicePlugin


def test_service_metadata():
    """Ensure service metadata is wired."""
    plugin = ExampleCacheServicePlugin()
    metadata = plugin.metadata

    assert metadata.name == "example_cache"
    assert metadata.version == "1.0.0"


def test_service_definition():
    """Ensure service definition is shaped correctly."""
    plugin = ExampleCacheServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["category"] == "core"
    assert "compose" in service_definition
    assert service_definition["compose"]["image"] == "redis:7-alpine"
