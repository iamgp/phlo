"""Integration tests for phlo-postgrest."""

import pytest

pytestmark = pytest.mark.integration


def test_postgrest_plugin_initializes():
    """Test that PostgREST plugin can be instantiated."""
    from phlo_postgrest.plugin import PostgrestServicePlugin

    plugin = PostgrestServicePlugin()
    assert plugin is not None
    assert plugin.metadata.name == "postgrest"


def test_postgrest_service_definition():
    """Test that service definition can be loaded."""
    from phlo_postgrest.plugin import PostgrestServicePlugin

    plugin = PostgrestServicePlugin()
    service_def = plugin.service_definition

    assert isinstance(service_def, dict)
