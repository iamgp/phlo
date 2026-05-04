"""Integration tests for phlo-grafana."""

import pytest

pytestmark = pytest.mark.integration


def test_grafana_plugin_initializes():
    """Test that Grafana plugin can be instantiated."""
    from phlo_grafana.plugin import GrafanaServicePlugin

    plugin = GrafanaServicePlugin()
    assert plugin is not None
    assert plugin.metadata.name == "grafana"


def test_grafana_service_definition():
    """Test that service definition can be loaded."""
    from phlo_grafana.plugin import GrafanaServicePlugin

    plugin = GrafanaServicePlugin()
    service_def = plugin.service_definition

    assert isinstance(service_def, dict)
    assert "grafana-data:/var/lib/grafana" in service_def["compose"]["volumes"]
    assert "./volumes/grafana:/var/lib/grafana" not in service_def["compose"]["volumes"]
