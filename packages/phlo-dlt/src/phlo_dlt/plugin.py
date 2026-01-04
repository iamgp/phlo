from __future__ import annotations

from collections.abc import Iterable

from phlo.capabilities.specs import AssetCheckSpec, AssetSpec
from phlo.plugins.base import AssetProviderPlugin, PluginMetadata

from phlo_dlt.decorator import get_ingestion_assets
from phlo_dlt.decorator import clear_ingestion_assets


class DltAssetProvider(AssetProviderPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dlt",
            version="0.1.0",
            description="DLT-based ingestion engine for Phlo",
        )

    def get_assets(self) -> Iterable[AssetSpec]:
        return get_ingestion_assets()

    def get_checks(self) -> Iterable[AssetCheckSpec]:
        return []

    def clear_registries(self) -> None:
        clear_ingestion_assets()
