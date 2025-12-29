"""Integration tests for phlo-postgres."""

import pytest

pytestmark = pytest.mark.integration


def test_postgres_plugin_initializes():
    """Test that Postgres plugin can be instantiated."""
    from phlo_postgres.plugin import PostgresServicePlugin

    plugin = PostgresServicePlugin()
    assert plugin is not None
    assert plugin.metadata.name == "postgres"


def test_postgres_service_definition():
    """Test that service definition can be loaded."""
    from phlo_postgres.plugin import PostgresServicePlugin

    plugin = PostgresServicePlugin()
    service_def = plugin.service_definition

    assert isinstance(service_def, dict)


def test_postgres_config_accessible():
    """Test Postgres configuration is accessible."""
    from phlo.config import get_settings

    settings = get_settings()
    assert hasattr(settings, "postgres_host")
    assert hasattr(settings, "postgres_port")
    assert hasattr(settings, "postgres_db")
