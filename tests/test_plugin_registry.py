"""Tests for plugin registry client."""

import time

from phlo.plugins import registry_client


def test_fetch_registry_uses_local_cache(monkeypatch):
    """Fetch registry falls back to bundled data when URL is empty."""
    sample_registry = {
        "version": "1.0.0",
        "plugins": {
            "example": {
                "type": "source",
                "package": "phlo-plugin-example",
                "version": "1.0.0",
                "description": "Example",
                "author": "Phlo Team",
                "tags": ["example"],
                "verified": True,
            }
        },
    }

    class DummySettings:
        plugin_registry_url = ""
        plugin_registry_cache_ttl_seconds = 3600
        plugin_registry_timeout_seconds = 1

    registry_client.clear_registry_cache()
    monkeypatch.setattr(registry_client, "get_settings", lambda: DummySettings())
    monkeypatch.setattr(registry_client, "_load_registry_from_local", lambda: sample_registry)

    registry = registry_client.fetch_registry(force_refresh=True)

    assert registry["plugins"]["example"]["package"] == "phlo-plugin-example"


def test_search_plugins_filters(monkeypatch):
    """Search filters by query, type, and tags."""
    sample_registry = {
        "version": "1.0.0",
        "plugins": {
            "alpha": {
                "type": "source",
                "package": "phlo-plugin-alpha",
                "version": "1.0.0",
                "description": "Alpha connector",
                "author": "Phlo Team",
                "tags": ["api", "alpha"],
                "verified": True,
            },
            "beta": {
                "type": "service",
                "package": "phlo-plugin-beta",
                "version": "1.0.0",
                "description": "Beta service",
                "author": "Phlo Team",
                "tags": ["service", "beta"],
                "verified": True,
            },
        },
    }

    class DummySettings:
        plugin_registry_url = ""
        plugin_registry_cache_ttl_seconds = 3600
        plugin_registry_timeout_seconds = 1

    registry_client.clear_registry_cache()
    monkeypatch.setattr(registry_client, "get_settings", lambda: DummySettings())
    registry_client._REGISTRY_CACHE["data"] = sample_registry
    registry_client._REGISTRY_CACHE["loaded_at"] = time.time()

    results = registry_client.search_plugins(query="alpha")
    assert len(results) == 1
    assert results[0].name == "alpha"

    results = registry_client.search_plugins(plugin_type="service")
    assert len(results) == 1
    assert results[0].name == "beta"

    results = registry_client.search_plugins(tags=["api"])
    assert len(results) == 1
    assert results[0].name == "alpha"
