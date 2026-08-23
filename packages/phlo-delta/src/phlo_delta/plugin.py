"""Delta Lake plugin for Phlo resource provider system.

This module provides the DeltaResourceProvider plugin that integrates
Delta Lake table storage capabilities into the Phlo framework.

Example:
    from phlo_delta.plugin import DeltaResourceProvider

    provider = DeltaResourceProvider()
    resources = provider.get_resources()

Loaded through the phlo plugin entry-point mechanism at startup rather than imported directly.
Registers Delta Lake table-store and schema-migration capabilities through phlo.capabilities.
"""

from __future__ import annotations

from phlo.capabilities import CapabilitySupport, ResourceSpec, SchemaMigrationSpec, TableStoreSpec
from phlo.plugins.base import PluginMetadata, ResourceProviderPlugin

from phlo_delta.resource import DeltaResource
from phlo_delta.schema_migrator import DeltaSchemaMigrator


class DeltaResourceProvider(ResourceProviderPlugin):
    """Resource provider plugin for Delta Lake access.

    This plugin exposes Delta Lake resources to the Phlo framework,
    providing table storage, schema migration, and time travel capabilities.

    Attributes:
        metadata: Plugin metadata including name, version, and capabilities.

    Example:
        provider = DeltaResourceProvider()
        table_stores = provider.get_table_stores()

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata.

        Returns:
            PluginMetadata: Metadata for the Delta Lake resource plugin,
                including name, version, description, and capability support.

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
            list[ResourceSpec]: Delta resource specifications containing
                the DeltaResource instance.

        """
        return [ResourceSpec(name="table_store", resource=DeltaResource())]

    def get_table_stores(self) -> list[TableStoreSpec]:
        """Get table-store capability specs exposed by this plugin.

        Returns:
            list[TableStoreSpec]: Delta table-store capability specifications
                with snapshot, schema evolution, and time travel support.

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
            list[SchemaMigrationSpec]: Delta schema migrator specifications
                with schema evolution support.

        """
        return [
            SchemaMigrationSpec(
                name="delta",
                provider=DeltaSchemaMigrator(),
                support=CapabilitySupport(supports_schema_evolution=True),
            )
        ]
