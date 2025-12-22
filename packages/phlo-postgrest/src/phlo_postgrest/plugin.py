"""Postgrest service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class PostgrestServicePlugin(ServicePlugin):
    """Service plugin for postgrest."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="postgrest",
            version="0.1.0",
            description="RESTful API automatically generated from PostgreSQL schema",
            author="Phlo Team",
            tags=['api', 'rest'],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_postgrest").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
