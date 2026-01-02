"""OpenMetadata service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class OpenMetadataServicePlugin(ServicePlugin):
    """Service plugin for OpenMetadata."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="openmetadata",
            version="0.1.0",
            description="OpenMetadata data catalog and governance",
            author="Phlo Team",
            tags=["catalog", "governance", "metadata"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_openmetadata").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
