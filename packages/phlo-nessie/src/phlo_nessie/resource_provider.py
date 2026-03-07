"""Capability provider for Nessie catalog/versioning resources."""

from __future__ import annotations

from phlo.capabilities import CapabilitySupport, CatalogScannerSpec, CatalogSpec, ResourceSpec
from phlo.plugins.base import PluginMetadata, ResourceProviderPlugin

from phlo_nessie.catalog_scanner import NessieTableScanner
from phlo_nessie.resource import NessieResource


class NessieResourceProvider(ResourceProviderPlugin):
    """Expose Nessie as a capability-native catalog/versioning provider."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the Nessie resource provider."""
        return PluginMetadata(
            name="nessie",
            version="0.1.0",
            description="Versioned catalog provider with branch and merge support",
        )

    def get_resources(self) -> list[ResourceSpec]:
        """Expose the raw Nessie client as a runtime resource."""
        return [ResourceSpec(name="catalog_versioning", resource=NessieResource())]

    def get_catalogs(self) -> list[CatalogSpec]:
        """Expose Nessie as a catalog capability."""
        support = CapabilitySupport(
            supports_refs=True,
            supports_snapshots=False,
            supports_promote=True,
        )
        return [
            CatalogSpec(
                name="nessie",
                provider=NessieResource(),
                support=support,
            )
        ]

    def get_catalog_scanners(self) -> list[CatalogScannerSpec]:
        """Expose Nessie table scanning as a capability."""
        return [
            CatalogScannerSpec(
                name="nessie",
                provider=NessieTableScanner.from_config(),
                support=CapabilitySupport(),
            )
        ]
