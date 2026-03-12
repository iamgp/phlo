"""Traefik service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class TraefikServicePlugin(ServicePlugin):
    """Service plugin for Traefik reverse proxy."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for Traefik service registration."""
        return PluginMetadata(
            name="traefik",
            version="0.1.0",
            description="Local reverse proxy for named service URLs",
            author="Phlo Team",
            tags=["networking", "proxy", "traefik"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load and return the Traefik service definition."""
        service_path = resources.files("phlo_traefik").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
