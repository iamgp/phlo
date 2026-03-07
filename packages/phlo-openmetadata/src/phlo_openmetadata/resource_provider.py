"""Resource provider plugin for OpenMetadata capabilities."""

from __future__ import annotations

from phlo.capabilities import MetadataCatalogSpec
from phlo.plugins import PluginMetadata, ResourceProviderPlugin

from phlo_openmetadata.metadata_catalog import OpenMetadataCatalogProvider


class OpenMetadataResourceProvider(ResourceProviderPlugin):
    """Expose OpenMetadata as a metadata catalog capability."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for resource discovery."""
        return PluginMetadata(
            name="openmetadata",
            version="0.1.0",
            description="OpenMetadata capability provider",
            tags=["catalog", "metadata"],
        )

    def get_resources(self) -> list:
        """OpenMetadata does not expose raw resources in this slice."""
        return []

    def get_metadata_catalogs(self) -> list[MetadataCatalogSpec]:
        """Expose OpenMetadata as a metadata catalog capability."""
        return [
            MetadataCatalogSpec(
                name="openmetadata",
                provider=OpenMetadataCatalogProvider(),
            )
        ]
