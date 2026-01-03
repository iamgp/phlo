from __future__ import annotations

from phlo.plugins.base import AssetProviderPlugin, PluginMetadata

from phlo_dbt.assets import build_dbt_asset_specs


class DbtAssetProvider(AssetProviderPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dbt",
            version="0.1.0",
            description="dbt models as Dagster assets",
        )

    def get_assets(self):
        return build_dbt_asset_specs()
