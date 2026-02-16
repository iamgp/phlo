"""Tests for Prometheus service plugin."""

from phlo_prometheus.plugin import PrometheusServicePlugin


def test_prometheus_service_definition():
    """Validate Prometheus service definition defaults."""
    plugin = PrometheusServicePlugin()
    defn = plugin.service_definition

    assert defn["name"] == "prometheus"
    assert defn["profile"] == "observability"


def test_prometheus_plugin_metadata():
    """Validate Prometheus plugin metadata."""
    plugin = PrometheusServicePlugin()
    meta = plugin.metadata

    assert meta.name == "prometheus"
    assert "observability" in meta.tags
