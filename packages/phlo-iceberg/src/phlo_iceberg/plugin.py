from __future__ import annotations

from phlo.capabilities import ResourceSpec
from phlo.plugins.base import PluginMetadata, ResourceProviderPlugin

from phlo_iceberg.resource import IcebergResource


class IcebergResourceProvider(ResourceProviderPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="iceberg",
            version="0.1.0",
            description="Iceberg/Nessie catalog resource for Phlo",
        )

    def get_resources(self) -> list[ResourceSpec]:
        return [ResourceSpec(name="iceberg", resource=IcebergResource())]
