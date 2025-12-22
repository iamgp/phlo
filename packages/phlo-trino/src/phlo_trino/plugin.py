"""Trino service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class TrinoServicePlugin(ServicePlugin):
    """Service plugin for Trino."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="trino",
            version="0.1.0",
            description="Distributed SQL query engine for the data lake",
            author="Phlo Team",
            tags=["core", "sql", "query"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_trino").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
