"""Grafana service plugin registration."""

from __future__ import annotations

from phlo.plugins import service_plugin_class


GrafanaServicePlugin = service_plugin_class(
    "GrafanaServicePlugin",
    name="grafana",
    version="0.1.0",
    description="Metrics visualization and dashboards",
    author="Phlo Team",
    tags=["observability", "metrics", "dashboards"],
)
