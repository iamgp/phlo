from __future__ import annotations

from collections.abc import Iterable

from phlo.capabilities.specs import AssetCheckSpec, AssetSpec
from phlo.plugins.base import AssetProviderPlugin, PluginMetadata

from phlo_dlt.decorator import get_ingestion_assets
from phlo_dlt.decorator import clear_ingestion_assets


class DltAssetProvider(AssetProviderPlugin):
    """Provide DLT-defined ingestion assets and checks to Phlo."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for discovery and registration.

        Returns:
            PluginMetadata: Static metadata for the DLT asset provider plugin.
        """
        return PluginMetadata(
            name="dlt",
            version="0.1.0",
            description="DLT-based ingestion engine for Phlo",
        )

    def get_assets(self) -> Iterable[AssetSpec]:
        """Return registered DLT ingestion assets.

        Returns:
            Iterable[AssetSpec]: Asset specifications discovered from DLT decorators.
        """
        return get_ingestion_assets()

    def get_checks(self) -> Iterable[AssetCheckSpec]:
        """Return asset checks exposed by this provider.

        Returns:
            Iterable[AssetCheckSpec]: Empty iterable because DLT provider has no checks.
        """
        return []

    def clear_registries(self) -> None:
        """Clear in-memory DLT ingestion asset registrations."""
        clear_ingestion_assets()
