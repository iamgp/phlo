"""Alloy service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class AlloyServicePlugin(ServicePlugin):
    """Service plugin for alloy."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="alloy",
            version="0.1.0",
            description="Grafana Alloy for log collection and shipping to Loki",
            author="Phlo Team",
            tags=['observability', 'logs', 'agent'],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_alloy").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
