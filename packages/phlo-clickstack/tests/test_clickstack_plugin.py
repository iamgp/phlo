"""Tests for ClickStack service plugin."""

from phlo_clickstack.plugin import ClickStackServicePlugin


def test_clickstack_service_definition() -> None:
    """Validate ClickStack service definition defaults."""
    plugin = ClickStackServicePlugin()
    defn = plugin.service_definition

    assert defn["name"] == "clickstack"
    assert defn["profile"] == "observability"


def test_clickstack_plugin_metadata() -> None:
    """Validate ClickStack plugin metadata."""
    plugin = ClickStackServicePlugin()
    meta = plugin.metadata

    assert meta.name == "clickstack"
    assert "observability" in meta.tags
