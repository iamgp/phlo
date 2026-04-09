"""Observatory service plugin for container orchestration.

This module defines the ServicePlugin implementation for the Observatory UI,
enabling Docker Compose-based deployment and lifecycle management through
the Phlo service orchestration system.

The ObservatoryServicePlugin provides:
    - Plugin metadata for discovery and versioning
    - Service definition loading from package resources
    - Integration with Phlo's service management CLI

Service Configuration:
    The service definition is loaded from service.yaml in the package resources,
    defining container images, ports, volumes, and environment variables.

Example:
    >>> from phlo_observatory.plugin import ObservatoryServicePlugin
    >>> plugin = ObservatoryServicePlugin()
    >>> print(plugin.metadata.name)
    'observatory'
    >>> service_def = plugin.service_definition

See Also:
    phlo.plugins.ServicePlugin: Base class for service plugins.
    phlo_observatory.service.yaml: Service definition configuration.

"""

from __future__ import annotations

from phlo.plugins import PackageYamlServicePlugin, PluginMetadata


class ObservatoryServicePlugin(PackageYamlServicePlugin):
    """Service plugin for the Observatory UI container orchestration.

    This plugin integrates the Observatory web interface with Phlo's service
    management system, enabling deployment via Docker Compose.

    Attributes:
        metadata: Plugin metadata including name, version, description, and tags.
        service_definition: Parsed Docker Compose service configuration.

    Example:
        >>> plugin = ObservatoryServicePlugin()
        >>> plugin.metadata.name
        'observatory'
        >>> 'image' in plugin.service_definition
        True

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the Observatory service.

        Provides static metadata used by Phlo's plugin discovery system to
        identify and categorize the Observatory service plugin.

        Returns:
            PluginMetadata with name, version, description, author, and tags.

        Example:
            >>> plugin = ObservatoryServicePlugin()
            >>> plugin.metadata.name
            'observatory'
            >>> 'ui' in plugin.metadata.tags
            True

        """
        return PluginMetadata(
            name="observatory",
            version="0.1.0",
            description="Phlo Observatory UI",
            author="Phlo Team",
            tags=["ui", "observability"],
        )
