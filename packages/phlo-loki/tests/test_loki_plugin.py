"""Tests for Loki service plugin."""

from phlo_loki.plugin import LokiServicePlugin


def test_loki_service_definition():
    """Validate Loki service definition fields."""

    plugin = LokiServicePlugin()
    defn = plugin.service_definition

    assert defn["name"] == "loki"
    assert defn["profile"] == "observability"


def test_loki_plugin_metadata():
    """Validate Loki plugin metadata tags and name."""

    plugin = LokiServicePlugin()
    meta = plugin.metadata

    assert meta.name == "loki"
    assert "observability" in meta.tags
