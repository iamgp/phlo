"""Traefik service plugin implementation.

This module defines the TraefikServicePlugin class which implements the ServicePlugin
interface for integrating Traefik reverse proxy into the Phlo service ecosystem.

Example:
    >>> plugin = TraefikServicePlugin()
    >>> metadata = plugin.metadata
    >>> print(metadata.name)
    'traefik'

"""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class TraefikServicePlugin(ServicePlugin):
    """Service plugin for Traefik reverse proxy.

    This plugin provides integration with Traefik, a modern HTTP reverse proxy
    and load balancer, enabling local service discovery and routing within the
    Phlo platform.

    Attributes:
        None

    Example:
        >>> plugin = TraefikServicePlugin()
        >>> definition = plugin.service_definition
        >>> print(definition['services']['traefik']['image'])

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for Traefik service registration.

        Returns:
            PluginMetadata containing plugin name, version, description,
            author, and tags for service discovery and documentation.

        Example:
            >>> plugin = TraefikServicePlugin()
            >>> metadata = plugin.metadata
            >>> print(metadata.name)
            'traefik'
            >>> print(metadata.version)
            '0.1.0'

        """
        return PluginMetadata(
            name="traefik",
            version="0.1.0",
            description="Local reverse proxy for named service URLs",
            author="Phlo Team",
            tags=["networking", "proxy", "traefik"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load and return the Traefik service definition.

        Reads the service.yaml configuration file from the package resources
        and returns it as a parsed Python dictionary.

        Returns:
            Dictionary containing the Docker Compose service definition
            for Traefik with container configuration, labels, and volumes.

        Raises:
            yaml.YAMLError: If the service.yaml file contains invalid YAML.
            FileNotFoundError: If the service.yaml file is missing.

        Example:
            >>> plugin = TraefikServicePlugin()
            >>> definition = plugin.service_definition
            >>> print(definition['services'].keys())

        """
        service_path = resources.files("phlo_traefik").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
