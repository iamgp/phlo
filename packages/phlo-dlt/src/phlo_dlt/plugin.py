from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Callable

from phlo.capabilities.specs import AssetCheckSpec, AssetSpec
from phlo.plugins.base import AssetProviderPlugin, IngestionProviderPlugin, PluginMetadata

from phlo_dlt.decorator import clear_ingestion_assets, get_ingestion_assets


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


class DLTIngestionProvider(IngestionProviderPlugin):
    """DLT-based ingestion provider for Phlo."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="dlt",
            version="0.1.0",
            description="DLT-based ingestion provider with pipeline orchestration",
        )

    def get_decorator(self) -> Callable:
        """Return the @phlo_ingestion decorator."""
        from phlo_dlt import phlo_ingestion

        return phlo_ingestion

    def get_asset_retriever(self) -> Callable[[], list[Any]]:
        """Return function to get registered ingestion assets."""
        return get_ingestion_assets
