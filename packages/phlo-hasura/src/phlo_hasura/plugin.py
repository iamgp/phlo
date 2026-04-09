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

from phlo.plugins import PackageYamlServicePlugin, PluginMetadata


class HasuraServicePlugin(PackageYamlServicePlugin):
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
