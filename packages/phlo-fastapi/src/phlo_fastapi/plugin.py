"""Fastapi service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class FastapiServicePlugin(ServicePlugin):
    """Service plugin for fastapi."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="fastapi",
            version="0.1.0",
            description="Custom FastAPI service with JWT auth and Trino query support",
            author="Phlo Team",
            tags=['api', 'fastapi', 'service'],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_fastapi").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
