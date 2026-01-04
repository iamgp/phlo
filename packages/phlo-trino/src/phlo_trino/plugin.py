"""Service and resource provider plugins for Trino."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.capabilities import ResourceSpec
from phlo.plugins import PluginMetadata, ResourceProviderPlugin, ServicePlugin
from phlo_trino.resource import TrinoResource


class TrinoServicePlugin(ServicePlugin):
    """Service plugin for Trino."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="trino",
            version="0.1.0",
            description="Distributed SQL query engine",
            author="Phlo Team",
            tags=["core", "query"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_trino").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))


class TrinoResourceProvider(ResourceProviderPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="trino",
            version="0.1.0",
            description="Trino resource for Phlo",
        )

    def get_resources(self) -> list[ResourceSpec]:
        return [ResourceSpec(name="trino", resource=TrinoResource())]
