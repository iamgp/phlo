"""Observatory service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class ObservatoryServicePlugin(ServicePlugin):
    """Service plugin for the Observatory UI."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="observatory",
            version="0.1.0",
            description="Phlo Observatory UI",
            author="Phlo Team",
            tags=["ui", "observability"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_observatory").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
