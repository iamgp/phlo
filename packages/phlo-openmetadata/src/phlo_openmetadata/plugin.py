"""OpenMetadata service plugin.

Provides OpenMetadata as a managed service within the Phlo plugin framework.
This plugin exposes service configuration and metadata for the OpenMetadata
data catalog and governance platform.

Example:
    >>> from phlo_openmetadata.plugin import OpenMetadataServicePlugin
    >>> plugin = OpenMetadataServicePlugin()
    >>> plugin.metadata.name
    'openmetadata'

"""

from __future__ import annotations

from phlo.plugins import PackageYamlServicePlugin, PluginMetadata


class OpenMetadataServicePlugin(PackageYamlServicePlugin):
    """Service plugin for OpenMetadata.

    Integrates OpenMetadata data catalog and governance platform into
    the Phlo service management system. Provides service definition
    metadata for container orchestration.

    Attributes:
        metadata: PluginMetadata containing plugin identification information.
        service_definition: YAML service configuration for deployment.

    Example:
        >>> plugin = OpenMetadataServicePlugin()
        >>> defn = plugin.service_definition
        >>> defn['services']
        {...}

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for OpenMetadata service registration.

        Returns:
            PluginMetadata: Metadata with name, version, description, and tags.

        """
        return PluginMetadata(
            name="openmetadata",
            version="0.1.0",
            description="OpenMetadata data catalog and governance",
            author="Phlo Team",
            tags=["catalog", "governance", "metadata"],
        )
