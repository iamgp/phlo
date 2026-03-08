"""ClickStack service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class ClickStackServicePlugin(ServicePlugin):
    """Service plugin for ClickStack."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for ClickStack service registration."""
        return PluginMetadata(
            name="clickstack",
            version="0.1.0",
            description="ClickStack all-in-one observability backend",
            author="Phlo Team",
            tags=["observability", "logs", "metrics", "traces"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load and return the ClickStack service definition."""
        service_path = resources.files("phlo_clickstack").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
