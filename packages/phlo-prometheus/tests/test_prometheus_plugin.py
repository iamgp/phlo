"""Tests for Prometheus service plugin."""

from phlo_prometheus.plugin import PrometheusServicePlugin


def test_prometheus_service_definition():
    plugin = PrometheusServicePlugin()
    defn = plugin.service_definition

    assert defn["name"] == "prometheus"
    assert defn["profile"] == "observability"


def test_prometheus_plugin_metadata():
    plugin = PrometheusServicePlugin()
    meta = plugin.metadata

    assert meta.name == "prometheus"
    assert "observability" in meta.tags
