"""Integration tests for phlo-nessie."""

import pytest

pytestmark = pytest.mark.integration


def test_nessie_plugin_initializes():
    """Test that Nessie plugin can be instantiated."""
    from phlo_nessie.plugin import NessieServicePlugin

    plugin = NessieServicePlugin()
    assert plugin is not None
    assert plugin.metadata.name == "nessie"


def test_nessie_service_definition():
    """Test that service definition can be loaded."""
    from phlo_nessie.plugin import NessieServicePlugin

    plugin = NessieServicePlugin()
    service_def = plugin.service_definition

    assert isinstance(service_def, dict)


def test_nessie_config_validation():
    """Test Nessie configuration is accessible."""
    from phlo.config import get_settings

    settings = get_settings()
    # Should have nessie-related settings
    assert hasattr(settings, "nessie_api_v1_uri") or hasattr(settings, "nessie_url")
