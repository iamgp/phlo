"""Nessie service plugin.

This module defines the Nessie service plugin for Phlo, providing Docker Compose
service definitions and metadata for the Nessie catalog service.

Example:
    >>> from phlo_nessie.plugin import NessieServicePlugin
    >>> plugin = NessieServicePlugin()
    >>> definition = plugin.service_definition

Classes:
    NessieServicePlugin: Service plugin for Nessie Docker orchestration.

"""

from __future__ import annotations

from phlo.plugins import PackageYamlServicePlugin, PluginMetadata


class NessieServicePlugin(PackageYamlServicePlugin):
    """Service plugin for Nessie.

    Provides Docker Compose service definitions and metadata for the
    Nessie catalog service within the Phlo plugin system.

    Attributes:
        metadata: Plugin identity, version, description, and tags.
        service_definition: Docker Compose service configuration dict.

    Example:
        >>> plugin = NessieServicePlugin()
        >>> print(plugin.metadata.name)
        'nessie'
        >>> definition = plugin.service_definition

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the Nessie service.

        Returns:
            PluginMetadata: Service identity including name, version,
                description, author, and capability tags.

        """
        return PluginMetadata(
            name="nessie",
            version="0.1.0",
            description="Git-like catalog for Iceberg tables with branch/merge support",
            author="Phlo Team",
            tags=["core", "catalog", "iceberg"],
        )
