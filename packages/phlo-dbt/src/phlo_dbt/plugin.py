"""Phlo plugin implementations for dbt integration.

This module provides the Phlo plugin classes that register dbt capabilities
with the Phlo platform. It includes both an AssetProviderPlugin (for exposing
dbt models as Phlo assets) and a TransformationProviderPlugin (for dbt-based
data transformations).

Example:
    >>> from phlo_dbt.plugin import DbtAssetProvider, DbtTransformationProvider
    >>>
    >>> # Get dbt assets
    >>> asset_provider = DbtAssetProvider()
    >>> assets = asset_provider.get_assets()
    >>>
    >>> # Get transformation provider
    >>> transform_provider = DbtTransformationProvider()
    >>> cli_plugin = transform_provider.get_cli_plugin()

"""

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
    """Asset provider plugin exposing dbt models as Phlo assets.

    This plugin discovers dbt models from the project's manifest and exposes
    them as Phlo AssetSpec objects. This enables dbt models to participate in
    Phlo's orchestration, lineage tracking, and monitoring systems.

    The plugin uses the build_dbt_asset_specs() function to parse the dbt
    manifest and create corresponding asset specifications with proper
    dependencies, metadata, and execution configuration.

    Example:
        >>> from phlo_dbt.plugin import DbtAssetProvider
        >>> provider = DbtAssetProvider()
        >>>
        >>> # Get plugin metadata
        >>> metadata = provider.metadata
        >>> print(f"Plugin: {metadata.name} v{metadata.version}")
        >>>
        >>> # Get dbt assets
        >>> assets = provider.get_assets()
        >>> for asset in assets:
        ...     print(f"Asset: {asset.key}, Group: {asset.group}")

    """

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
    """Transformation provider plugin for dbt.

    This plugin registers dbt as a transformation provider in Phlo, enabling
    dbt models to be executed as part of Phlo's data pipeline transformations.

    The provider supplies both the asset retriever (for discovering transformable
    assets) and the CLI plugin (for dbt-related CLI commands). This allows Phlo
    to integrate dbt runs into its orchestration and provide unified CLI access
    to dbt operations.

    Example:
        >>> from phlo_dbt.plugin import DbtTransformationProvider
        >>> provider = DbtTransformationProvider()
        >>>
        >>> # Get metadata
        >>> metadata = provider.metadata
        >>> print(f"Transform Provider: {metadata.name}")
        >>>
        >>> # Get asset retriever function
        >>> retriever = provider.get_asset_retriever()
        >>> assets = retriever()
        >>>
        >>> # Get CLI plugin for dbt commands
        >>> cli = provider.get_cli_plugin()
            >>> commands = cli.get_cli_commands()

    """

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
        """Return a function to retrieve transformation asset specs.

        Returns:
            Callable that returns dbt asset specifications.

        """
        return build_dbt_asset_specs

    def get_cli_plugin(self):
        """Return the CLI plugin for dbt commands.

        Returns:
            DbtCliPlugin instance for dbt CLI command integration.

        """
        from phlo_dbt.cli_plugin import DbtCliPlugin

        return DbtCliPlugin
