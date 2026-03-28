"""Loki service plugin for Docker Compose orchestration.

This module provides the LokiServicePlugin class which registers Loki as a
managed service in the Phlo platform. It loads service configuration from
a YAML file bundled with the package.

Example:
    The plugin is auto-discovered by Phlo::

        from phlo.plugins import load_plugin
        plugin = load_plugin("phlo_loki")

Attributes:
    LokiServicePlugin: Service plugin class for Loki container management.

"""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class LokiServicePlugin(ServicePlugin):
    """Service plugin for Loki log aggregation.

    This plugin manages the lifecycle of a Loki container for log aggregation
    and querying within the Phlo platform. It provides Docker Compose service
    configuration loaded from package resources.

    Attributes:
        None - Properties are computed dynamically.

    Example:
        Plugin is instantiated by the discovery system::

            plugin = LokiServicePlugin()
            metadata = plugin.metadata
            services = plugin.service_definition

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the Loki service.

        Returns:
            Static metadata used for plugin discovery.

        """
        return PluginMetadata(
            name="loki",
            version="0.1.0",
            description="Log aggregation and querying",
            author="Phlo Team",
            tags=["observability", "logs"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load the Loki service definition from package resources.

        Returns:
            Parsed compose-style service configuration.

        """
        service_path = resources.files("phlo_loki").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
