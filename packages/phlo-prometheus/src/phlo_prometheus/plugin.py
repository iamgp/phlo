"""Prometheus service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class PrometheusServicePlugin(ServicePlugin):
    """Service plugin for prometheus."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="prometheus",
            version="0.1.0",
            description="Metrics collection and monitoring",
            author="Phlo Team",
            tags=['observability', 'metrics'],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_prometheus").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
