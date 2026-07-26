"""Tests for Postgres service and resource plugins."""

from phlo.capabilities import PublishTargetSpec
from phlo_postgres.plugin import PostgresResourceProvider, PostgresServicePlugin
from phlo_postgres.publish_target import PostgresPublishTarget


def test_postgres_service_definition():
    """Validate Postgres service definition fields."""
    plugin = PostgresServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "postgres"
    assert service_definition["category"] == "core"


def test_postgres_service_builds_pinned_hardened_image() -> None:
    service_definition = PostgresServicePlugin().service_definition

    assert service_definition["image"] == "phlo/postgres:18.4-alpine3.24-gosu1.19"
    assert service_definition["build"]["dockerfile"] == "postgres/Dockerfile"


def test_postgres_resource_provider():
    """Validate Postgres resource provider output."""
    provider = PostgresResourceProvider()
    resources = provider.get_resources()

    assert len(resources) == 1
    assert resources[0].name == "postgres"


def test_postgres_resource_provider_exposes_publish_target() -> None:
    provider = PostgresResourceProvider()
    publish_targets = provider.get_publish_targets()

    assert publish_targets == [
        PublishTargetSpec(
            name="postgres",
            provider=PostgresPublishTarget(),
            metadata={"target_system": "postgres", "role": "serving"},
        )
    ]
