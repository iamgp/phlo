from __future__ import annotations

from collections.abc import Iterable

from phlo.capabilities.specs import AssetSpec
from phlo.plugins.base import (
    AssetProviderPlugin,
    PluginMetadata,
    TransformationProviderPlugin,
)

from phlo_dbt.assets import build_dbt_asset_specs


class DbtAssetProvider(AssetProviderPlugin):
    """Asset provider plugin exposing dbt assets."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            Metadata describing the dbt asset provider plugin.
        """
        return PluginMetadata(
            name="dbt",
            version="0.1.0",
            description="dbt models as asset specs",
        )

    def get_assets(self) -> Iterable[AssetSpec]:
        """Return dbt-derived asset specifications.

        Returns:
            Iterable of dbt asset specifications.
        """
        return build_dbt_asset_specs()


class DbtTransformationProvider(TransformationProviderPlugin):
    """Transformation provider plugin for dbt."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            Metadata describing the dbt transformation provider plugin.
        """
        return PluginMetadata(
            name="dbt",
            version="0.1.0",
            description="dbt-based transformation provider",
        )

    def get_asset_retriever(self):
        """Return a function to retrieve transformation asset specs."""
        return build_dbt_asset_specs

    def get_cli_plugin(self):
        """Return the CLI plugin for dbt commands."""
        from phlo_dbt.cli_plugin import DbtCliPlugin

        return DbtCliPlugin
