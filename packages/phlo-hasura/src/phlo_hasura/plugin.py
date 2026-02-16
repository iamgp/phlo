"""Hasura service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class HasuraServicePlugin(ServicePlugin):
    """Service plugin for hasura."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the Hasura service."""
        return PluginMetadata(
            name="hasura",
            version="0.1.0",
            description="GraphQL API engine with real-time subscriptions",
            author="Phlo Team",
            tags=["api", "graphql"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Return the Docker service definition for Hasura."""
        service_path = resources.files("phlo_hasura").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
