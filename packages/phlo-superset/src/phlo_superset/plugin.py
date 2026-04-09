"""Superset service plugin for Phlo.

This module provides the plugin implementation for integrating Apache Superset
as a managed service within the Phlo platform. It exposes service metadata
and Docker Compose definitions through the Phlo plugin system.

Example:
    >>> from phlo_superset.plugin import SupersetServicePlugin
    >>> plugin = SupersetServicePlugin()
    >>> print(plugin.metadata.name)
    'superset'

"""

from __future__ import annotations

from phlo.plugins import PackageYamlServicePlugin, PluginMetadata


class SupersetServicePlugin(PackageYamlServicePlugin):
    """Service plugin for Apache Superset.

    This plugin integrates Apache Superset business intelligence and data
    visualization capabilities into the Phlo service orchestration system.
    It provides Docker service definitions and metadata for the Superset
    BI platform.

    Attributes:
        metadata: PluginMetadata with name, version, description, and tags.
        service_definition: Docker Compose service configuration as dict.

    Example:
        >>> plugin = SupersetServicePlugin()
        >>> print(plugin.metadata.description)
        'Apache Superset for business intelligence and data visualization'

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the Superset service.

        Returns:
            PluginMetadata containing service identification, versioning,
            and categorization information for the plugin registry.

        Example:
            >>> plugin = SupersetServicePlugin()
            >>> meta = plugin.metadata
            >>> print(meta.name, meta.version)
            'superset 0.1.0'

        """
        return PluginMetadata(
            name="superset",
            version="0.1.0",
            description="Apache Superset for business intelligence and data visualization",
            author="Phlo Team",
            tags=["bi", "superset", "visualization"],
        )
