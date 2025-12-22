"""Tests for Dagster service plugin."""

from phlo_dagster.plugin import DagsterServicePlugin


def test_dagster_service_definition():
    plugin = DagsterServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "dagster"
    assert service_definition["category"] == "orchestration"
