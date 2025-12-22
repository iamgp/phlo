"""Tests for Postgres service plugin."""

from phlo_postgres.plugin import PostgresServicePlugin


def test_postgres_service_definition():
    plugin = PostgresServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "postgres"
    assert service_definition["category"] == "core"
