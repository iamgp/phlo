"""Tests for ClickHouse service plugin."""

from phlo_clickhouse.plugin import ClickHouseServicePlugin


def test_clickhouse_service_definition():
    """Validate ClickHouse service definition fields."""

    plugin = ClickHouseServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "clickhouse"
    assert service_definition["category"] == "data"


def test_clickhouse_service_metadata():
    """Validate ClickHouse service plugin metadata."""

    plugin = ClickHouseServicePlugin()
    metadata = plugin.metadata

    assert metadata.name == "clickhouse"
    assert metadata.version == "0.1.0"
    assert "data" in metadata.tags
    assert "query" in metadata.tags
    assert "storage" in metadata.tags
