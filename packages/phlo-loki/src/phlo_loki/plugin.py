"""Loki service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class LokiServicePlugin(ServicePlugin):
    """Service plugin for loki."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="loki",
            version="0.1.0",
            description="Log aggregation and querying",
            author="Phlo Team",
            tags=['observability', 'logs'],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_loki").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
