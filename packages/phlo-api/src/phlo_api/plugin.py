"""Phlo API service plugin.

This module provides the ServicePlugin implementation for the Phlo API backend,
integrating with the phlo plugin system to register the API service definition.

Classes:
    PhloApiServicePlugin: Service plugin for the Phlo API backend.

Example:
    The plugin is automatically discovered and loaded by the phlo plugin system:

    .. code-block:: python

        from phlo.plugins.discovery import ServiceDiscovery

        discovery = ServiceDiscovery()
        service = discovery.get_service("phlo-api")
        print(service.name)  # "phlo-api"

"""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class PhloApiServicePlugin(ServicePlugin):
    """Service plugin for the Phlo API backend.

    This plugin registers the Phlo API as a discoverable service within
    the phlo ecosystem. It provides metadata about the service and
    exposes the Docker Compose service definition.

    The plugin reads its service definition from the embedded service.yaml
    file within the phlo_api package.

    Attributes:
        metadata: Plugin metadata including name, version, and description.
        service_definition: Docker Compose service configuration dict.

    Example:
        .. code-block:: python

            plugin = PhloApiServicePlugin()
            meta = plugin.metadata
            print(f"{meta.name} v{meta.version}")

            service_def = plugin.service_definition
            print(service_def["services"]["phlo-api"]["image"])

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the Phlo API service.

        Returns:
            PluginMetadata: Metadata containing name, version, description,
                author, and tags for the plugin.

        Example:
            .. code-block:: python

                plugin = PhloApiServicePlugin()
                meta = plugin.metadata
                assert meta.name == "phlo-api"
                assert "api" in meta.tags

        """
        return PluginMetadata(
            name="phlo-api",
            version="0.1.0",
            description="Backend API exposing Phlo internals to Observatory",
            author="Phlo Team",
            tags=["api", "observability"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Return the Docker service definition for the Phlo API.

        Loads and parses the service.yaml file embedded in the phlo_api
        package. This YAML defines the Docker Compose service configuration
        including image, ports, environment, and dependencies.

        Returns:
            dict[str, Any]: Parsed Docker Compose service definition.

        Raises:
            FileNotFoundError: If service.yaml is missing from the package.
            yaml.YAMLError: If service.yaml contains invalid YAML.

        Example:
            .. code-block:: python

                plugin = PhloApiServicePlugin()
                service_def = plugin.service_definition
                services = service_def.get("services", {})
                phlo_api = services.get("phlo-api", {})
                ports = phlo_api.get("ports", [])

        """
        service_path = resources.files("phlo_api").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
