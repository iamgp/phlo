"""Phlo API service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class PhloApiServicePlugin(ServicePlugin):
    """Service plugin for the Phlo API backend."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="phlo-api",
            version="0.1.0",
            description="Backend API exposing Phlo internals to Observatory",
            author="Phlo Team",
            tags=["api", "observability"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_api").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
