"""PostgREST service plugin for Phlo.

This module provides the service plugin implementation that registers PostgREST
as a managed service within the Phlo ecosystem. It handles service metadata and
Docker Compose configuration.

Classes:
    PostgrestServicePlugin: Service plugin for PostgREST container management.

Example:
    The plugin is automatically discovered by Phlo's plugin system:

    >>> from phlo.plugins import get_plugin
    >>> plugin = get_plugin("postgrest")
    >>> plugin.metadata.name
    'postgrest'

"""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class PostgrestServicePlugin(ServicePlugin):
    """Service plugin for managing PostgREST container lifecycle.

    This plugin integrates PostgREST with Phlo's service management system,
    providing Docker Compose configuration and metadata for the REST API
    service automatically generated from PostgreSQL schemas.

    Attributes:
        metadata (PluginMetadata): Plugin identification and version info.
        service_definition (dict[str, Any]): Docker Compose service configuration.

    Example:
        >>> plugin = PostgrestServicePlugin()
        >>> plugin.metadata.name
        'postgrest'
        >>> plugin.metadata.tags
        ['api', 'rest']

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the PostgREST service.

        Returns:
            PluginMetadata containing:
                - name: Service identifier ('postgrest')
                - version: Plugin version ('0.1.0')
                - description: Human-readable description
                - author: Plugin maintainer ('Phlo Team')
                - tags: Service category tags

        Example:
            >>> plugin = PostgrestServicePlugin()
            >>> meta = plugin.metadata
            >>> meta.name, meta.version
            ('postgrest', '0.1.0')

        """
        return PluginMetadata(
            name="postgrest",
            version="0.1.0",
            description="RESTful API automatically generated from PostgreSQL schema",
            author="Phlo Team",
            tags=["api", "rest"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Return the Docker service definition for PostgREST.

        Loads the service configuration from the embedded service.yaml file
        which defines the Docker Compose service specification including
        ports, environment variables, and dependencies.

        Returns:
            dict[str, Any]: Docker Compose service definition parsed from YAML.

        Raises:
            FileNotFoundError: If service.yaml is missing from the package.
            yaml.YAMLError: If service.yaml contains invalid YAML.

        Example:
            >>> plugin = PostgrestServicePlugin()
            >>> config = plugin.service_definition
            >>> 'image' in config or 'build' in config
            True

        """
        service_path = resources.files("phlo_postgrest").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
