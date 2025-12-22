"""Grafana service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class GrafanaServicePlugin(ServicePlugin):
    """Service plugin for grafana."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="grafana",
            version="0.1.0",
            description="Metrics visualization and dashboards",
            author="Phlo Team",
            tags=['observability', 'metrics', 'dashboards'],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_grafana").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
