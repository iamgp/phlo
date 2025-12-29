"""Integration tests for phlo-trino."""

import pytest

pytestmark = pytest.mark.integration


def test_trino_plugin_initializes():
    """Test that Trino plugin can be instantiated."""
    from phlo_trino.plugin import TrinoServicePlugin

    plugin = TrinoServicePlugin()
    assert plugin is not None
    assert plugin.metadata.name == "trino"


def test_trino_service_definition():
    """Test that service definition can be loaded."""
    from phlo_trino.plugin import TrinoServicePlugin

    plugin = TrinoServicePlugin()
    service_def = plugin.service_definition

    assert isinstance(service_def, dict)


def test_trino_config_accessible():
    """Test Trino configuration is accessible."""
    from phlo.config import get_settings

    settings = get_settings()
    assert hasattr(settings, "trino_host")
    assert hasattr(settings, "trino_port")
