from __future__ import annotations

from collections.abc import Iterable

from phlo.capabilities.specs import AssetSpec
from phlo.plugins.base import AssetProviderPlugin, PluginMetadata

from phlo_dbt.assets import build_dbt_asset_specs


class DbtAssetProvider(AssetProviderPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dbt",
            version="0.1.0",
            description="dbt models as asset specs",
        )

    def get_assets(self) -> Iterable[AssetSpec]:
        return build_dbt_asset_specs()
