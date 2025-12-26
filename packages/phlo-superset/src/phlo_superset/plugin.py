"""Superset service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class SupersetServicePlugin(ServicePlugin):
    """Service plugin for superset."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="superset",
            version="0.1.0",
            description="Apache Superset for business intelligence and data visualization",
            author="Phlo Team",
            tags=["bi", "superset", "visualization"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_superset").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
