"""Tests for Postgres service and resource plugins."""

from phlo_postgres.plugin import PostgresResourceProvider, PostgresServicePlugin


def test_postgres_service_definition():
    plugin = PostgresServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "postgres"
    assert service_definition["category"] == "core"


def test_postgres_resource_provider():
    provider = PostgresResourceProvider()
    resources = provider.get_resources()

    assert len(resources) == 1
    assert resources[0].name == "postgres"
