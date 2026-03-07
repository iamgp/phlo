from __future__ import annotations

from phlo.capabilities import CapabilitySupport, ResourceSpec, SchemaMigrationSpec, TableStoreSpec
from phlo.plugins.base import PluginMetadata, ResourceProviderPlugin

from phlo_delta.resource import DeltaResource
from phlo_delta.schema_migrator import DeltaSchemaMigrator


class DeltaResourceProvider(ResourceProviderPlugin):
    """Resource provider plugin for Delta Lake access."""

    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata.

        Returns:
            PluginMetadata: Metadata for the Delta Lake resource plugin.
        """
        return PluginMetadata(
            name="delta",
            version="0.1.0",
            description="Delta Lake table-store resource for Phlo",
            support=CapabilitySupport(
                supports_snapshots=True,
                supports_schema_evolution=True,
                supports_time_travel=True,
            ),
        )

    def get_resources(self) -> list[ResourceSpec]:
        """Get resource specs exposed by this plugin.

        Returns:
            list[ResourceSpec]: Delta resource specifications.
        """
        return [ResourceSpec(name="table_store", resource=DeltaResource())]

    def get_table_stores(self) -> list[TableStoreSpec]:
        """Get table-store capability specs exposed by this plugin.

        Returns:
            list[TableStoreSpec]: Delta table-store capability specifications.
        """
        return [
            TableStoreSpec(
                name="delta",
                provider=DeltaResource(),
                support=CapabilitySupport(
                    supports_snapshots=True,
                    supports_schema_evolution=True,
                    supports_time_travel=True,
                ),
            )
        ]

    def get_schema_migrators(self) -> list[SchemaMigrationSpec]:
        """Get schema-migrator capability specs exposed by this plugin.

        Returns:
            list[SchemaMigrationSpec]: Delta schema migrator specifications.
        """
        return [
            SchemaMigrationSpec(
                name="delta",
                provider=DeltaSchemaMigrator(),
                support=CapabilitySupport(supports_schema_evolution=True),
            )
        ]
