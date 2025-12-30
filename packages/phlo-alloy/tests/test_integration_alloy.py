"""Integration tests for phlo-alloy."""

import pytest

pytestmark = pytest.mark.integration


def test_alloy_plugin_initializes():
    """Test that Alloy plugin can be instantiated."""
    from phlo_alloy.plugin import AlloyServicePlugin

    plugin = AlloyServicePlugin()
    assert plugin is not None
    assert plugin.metadata.name == "alloy"


def test_alloy_service_definition():
    """Test that service definition can be loaded."""
    from phlo_alloy.plugin import AlloyServicePlugin

    plugin = AlloyServicePlugin()
    service_def = plugin.service_definition

    assert isinstance(service_def, dict)
