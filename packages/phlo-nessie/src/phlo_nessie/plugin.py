"""Nessie service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class NessieServicePlugin(ServicePlugin):
    """Service plugin for Nessie."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="nessie",
            version="0.1.0",
            description="Git-like catalog for Iceberg tables with branch/merge support",
            author="Phlo Team",
            tags=["core", "catalog", "iceberg"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_nessie").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
