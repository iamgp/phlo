"""ClickStack service plugin.

This module defines the ClickStackServicePlugin class which provides
service registration and definition for the ClickStack observability
backend service.
"""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class ClickStackServicePlugin(ServicePlugin):
    """Service plugin for ClickStack.

    Provides ClickStack (ClickHouse-based observability backend) as a
    managed service within the Phlo services framework. The service
    definition is loaded from the bundled service.yaml file.

    Example:
        Plugin is automatically discovered via entry points.
        Service is started with `phlo services start clickstack`.

    Attributes:
        service_definition: ClickStack Docker Compose configuration.

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for ClickStack service registration.

        Returns:
            PluginMetadata: Metadata including name, version, description,
                author, and tags for discovery.

        """
        return PluginMetadata(
            name="clickstack",
            version="0.1.0",
            description="ClickStack all-in-one observability backend",
            author="Phlo Team",
            tags=["observability", "logs", "metrics", "traces"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load and return the ClickStack service definition.

        Reads the service.yaml file from the package resources and
        parses it as YAML to produce the service configuration dict.

        Returns:
            dict[str, Any]: Parsed Docker Compose service configuration.

        Raises:
            yaml.YAMLError: If service.yaml contains invalid YAML.
            FileNotFoundError: If service.yaml is missing from package.

        """
        service_path = resources.files("phlo_clickstack").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
