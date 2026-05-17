"""Tests for ClickHouse service plugin."""

from click.testing import CliRunner

from phlo_clickhouse.cli import clickhouse_group
from phlo_clickhouse.plugin import ClickHouseServicePlugin


def test_clickhouse_service_definition():
    """Validate ClickHouse service definition fields."""

    plugin = ClickHouseServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "clickhouse"
    assert service_definition["category"] == "data"
    assert "clickhouse-data:/var/lib/clickhouse" in service_definition["compose"]["volumes"]
    assert "clickhouse-logs:/var/log/clickhouse-server" in service_definition["compose"]["volumes"]


def test_clickhouse_service_metadata():
    """Validate ClickHouse service plugin metadata."""

    plugin = ClickHouseServicePlugin()
    metadata = plugin.metadata

    assert metadata.name == "clickhouse"
    assert metadata.version == "0.1.0"
    assert "data" in metadata.tags
    assert "query" in metadata.tags
    assert "storage" in metadata.tags


def test_clickhouse_query_rejects_missing_input(monkeypatch):
    """Query command should fail with the shared SQL input contract."""
    monkeypatch.setattr("phlo_clickhouse.cli._ensure_phlo_dir", lambda: None)
    monkeypatch.setattr("phlo_clickhouse.cli._require_container_backend", lambda: None)
    monkeypatch.setattr("phlo_clickhouse.cli.get_project_name", lambda: "demo")

    result = CliRunner().invoke(clickhouse_group, ["query"])

    assert result.exit_code != 0
    assert "Error: no SQL query provided" in result.output
    assert "Provide an inline query argument or pass --file." in result.output
    assert 'Run: phlo clickhouse query "SELECT 1"' in result.output
