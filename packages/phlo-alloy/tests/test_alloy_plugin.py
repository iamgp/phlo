"""Tests for Alloy service plugin."""

from phlo_alloy.plugin import AlloyServicePlugin


def test_alloy_service_definition():
    plugin = AlloyServicePlugin()
    defn = plugin.service_definition

    assert defn["name"] == "alloy"
    assert defn["profile"] == "observability"


def test_alloy_plugin_metadata():
    plugin = AlloyServicePlugin()
    meta = plugin.metadata

    assert meta.name == "alloy"
    assert "observability" in meta.tags
