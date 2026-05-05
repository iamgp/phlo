"""Tests for ClickStack service plugin."""

from phlo_clickstack.plugin import ClickStackServicePlugin


def test_clickstack_service_definition() -> None:
    """Validate ClickStack service definition defaults."""
    plugin = ClickStackServicePlugin()
    defn = plugin.service_definition

    assert defn["name"] == "clickstack"
    assert defn["profile"] == "observability"
    assert "${CLICKSTACK_PORT:-18080}:8080" in defn["compose"]["ports"]
    assert "${CLICKSTACK_HTTP_PORT:-18123}:8123" in defn["compose"]["ports"]
    assert "${CLICKSTACK_NATIVE_PORT:-19002}:9000" in defn["compose"]["ports"]
    assert not any("4317" in port or "4318" in port for port in defn["compose"]["ports"])
    assert "clickstack-data:/var/lib/clickhouse" in defn["compose"]["volumes"]
    assert "./volumes/clickstack:/var/lib/clickhouse" not in defn["compose"]["volumes"]


def test_clickstack_plugin_metadata() -> None:
    """Validate ClickStack plugin metadata."""
    plugin = ClickStackServicePlugin()
    meta = plugin.metadata

    assert meta.name == "clickstack"
    assert "observability" in meta.tags
