from __future__ import annotations

from phlo.capabilities import ResourceSpec
from phlo.plugins.base import PluginMetadata, ResourceProviderPlugin

from phlo_iceberg.resource import IcebergResource


class IcebergResourceProvider(ResourceProviderPlugin):
    """Resource provider plugin for Iceberg access."""

    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata.

        Returns:
            PluginMetadata: Metadata for the Iceberg resource plugin.
        """
        return PluginMetadata(
            name="iceberg",
            version="0.1.0",
            description="Iceberg/Nessie catalog resource for Phlo",
        )

    def get_resources(self) -> list[ResourceSpec]:
        """Get resource specs exposed by this plugin.

        Returns:
            list[ResourceSpec]: Iceberg resource specifications.
        """
        return [ResourceSpec(name="iceberg", resource=IcebergResource())]
