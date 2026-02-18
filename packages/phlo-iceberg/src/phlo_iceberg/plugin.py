from __future__ import annotations

from phlo.capabilities import ResourceSpec, TableStoreSpec
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
        return [ResourceSpec(name="table_store", resource=IcebergResource())]

    def get_table_stores(self) -> list[TableStoreSpec]:
        """Get table-store capability specs exposed by this plugin.

        Returns:
            list[TableStoreSpec]: Iceberg table-store capability specifications.
        """
        return [TableStoreSpec(name="iceberg", provider=IcebergResource())]
