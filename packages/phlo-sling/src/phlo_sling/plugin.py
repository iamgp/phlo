"""Sling service and ingestion plugins."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from phlo.capabilities.specs import AssetCheckSpec, AssetSpec
from phlo.plugins.base import AssetProviderPlugin, IngestionProviderPlugin, PluginMetadata

from phlo_sling.decorator import clear_sling_assets, get_sling_assets


class SlingAssetProvider(AssetProviderPlugin):
    """Provide Sling-defined replication assets and checks to Phlo."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for discovery and registration."""
        return PluginMetadata(
            name="sling",
            version="0.1.0",
            description="Sling-based replication engine for Phlo",
        )

    def get_assets(self) -> Iterable[AssetSpec]:
        """Return registered Sling replication assets."""
        return get_sling_assets()

    def get_checks(self) -> Iterable[AssetCheckSpec]:
        """Return asset checks exposed by this provider."""
        return []

    def clear_registries(self) -> None:
        """Clear in-memory Sling replication asset registrations."""
        clear_sling_assets()


class SlingIngestionProvider(IngestionProviderPlugin):
    """Sling-based ingestion provider for Phlo."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="sling",
            version="0.1.0",
            description="Sling-based replication provider with database replication",
        )

    def get_decorator(self) -> Callable:
        """Return the @phlo_sling_replication decorator."""
        from phlo_sling import phlo_sling_replication

        return phlo_sling_replication

    def get_asset_retriever(self) -> Callable[[], list[Any]]:
        """Return function to get registered replication assets."""
        return get_sling_assets
