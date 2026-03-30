"""Hasura service plugin.

This module provides the HasuraServicePlugin class that integrates Hasura
with the Phlo plugin system. It exposes service metadata and Docker service
definitions for the Hasura GraphQL engine.

Example:
    >>> from phlo_hasura.plugin import HasuraServicePlugin
    >>> plugin = HasuraServicePlugin()
    >>> plugin.metadata.name
    'hasura'
    >>> service_def = plugin.service_definition

"""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class HasuraServicePlugin(ServicePlugin):
    """Service plugin for Hasura GraphQL engine.

    Integrates Hasura with the Phlo service management system, providing
    Docker service definitions and metadata for the GraphQL API engine.

    Attributes:
        _metadata: Cached plugin metadata.
        _service_definition: Cached service definition loaded from service.yaml.

    Example:
        >>> plugin = HasuraServicePlugin()
        >>> plugin.metadata.name
        'hasura'
        >>> plugin.metadata.tags
        ['api', 'graphql']
        >>> service = plugin.service_definition

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the Hasura service.

        Returns:
            PluginMetadata containing:
                - name: Service identifier ('hasura')
                - version: Plugin version
                - description: Service description
                - author: Plugin author
                - tags: Service category tags

        Example:
            >>> plugin = HasuraServicePlugin()
            >>> meta = plugin.metadata
            >>> print(meta.name, meta.version)
            hasura 0.1.0

        """
        return PluginMetadata(
            name="hasura",
            version="0.1.0",
            description="GraphQL API engine with real-time subscriptions",
            author="Phlo Team",
            tags=["api", "graphql"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Return the Docker service definition for Hasura.

        Loads the service.yaml file from the package resources and
        returns it as a parsed dictionary. This defines the Docker
        Compose service configuration for the Hasura container.

        Returns:
            Dictionary containing Docker service definition.

        Raises:
            FileNotFoundError: If service.yaml is not found in package resources.
            yaml.YAMLError: If service.yaml contains invalid YAML.

        Example:
            >>> plugin = HasuraServicePlugin()
            >>> service = plugin.service_definition
            >>> print(service['services']['hasura']['image'])
            hasura/graphql-engine:latest

        """
        service_path = resources.files("phlo_hasura").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
