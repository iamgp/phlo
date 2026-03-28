"""Plugin interface for Phlo DLT integration.

This module provides the plugin classes that integrate phlo-dlt with the
Phlo plugin system. It exposes DLT-based ingestion capabilities through
standardized plugin interfaces.

Plugin Classes:
    - :class:`DltAssetProvider`: Provides DLT-defined assets to Phlo
    - :class:`DLTIngestionProvider`: Provides ingestion decorator interface

Plugin Registration:
    These plugins are discovered via entry points defined in pyproject.toml:
    - ``phlo.asset_providers``: DltAssetProvider
    - ``phlo.ingestion_providers``: DLTIngestionProvider

Capabilities Exposed:
    - Ingestion asset definitions from @phlo_ingestion decorators
    - Asset check specifications for Pandera validation
    - The phlo_ingestion decorator for users

See Also:
    - :mod:`phlo.plugins.base`: Base plugin interfaces
    - :mod:`phlo.plugins.discovery`: Plugin discovery system
    - :mod:`phlo_dlt.decorator`: Asset registration source

Example:
    The plugins are auto-discovered by Phlo. Users interact with them
    via the public API:
    ```python
    import phlo

    # Uses DLTIngestionProvider internally
    @phlo.ingestion.phlo_ingestion(table_name="users", ...)
    def load_users(): ...

    # Uses DltAssetProvider internally
    assets = phlo.ingestion.get_ingestion_assets()
    ```

"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Callable

from phlo.capabilities.specs import AssetCheckSpec, AssetSpec
from phlo.plugins.base import AssetProviderPlugin, IngestionProviderPlugin, PluginMetadata

from phlo_dlt.decorator import clear_ingestion_assets, get_ingestion_assets


class DltAssetProvider(AssetProviderPlugin):
    """Provide DLT-defined ingestion assets and checks to Phlo.

    Asset provider plugin that exposes all ingestion assets registered
    via the ``@phlo_ingestion`` decorator. Discovered by Phlo's plugin
    system and used during asset loading.

    Attributes:
        metadata: Static plugin metadata for discovery.

    Methods:
        get_assets: Return all registered DLT ingestion assets.
        get_checks: Return asset check specs (currently empty).
        clear_registries: Clear internal asset registry.

    Example:
        This class is auto-discovered by Phlo. Users don't instantiate it:
        ```python
        # In Phlo internals, this happens:
        from phlo_dlt.plugin import DltAssetProvider
        provider = DltAssetProvider()
        assets = list(provider.get_assets())
        ```

    """

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
            Checks are attached to individual assets, not the provider.

        """
        return []

    def clear_registries(self) -> None:
        """Clear in-memory DLT ingestion asset registrations.

        Removes all registered assets from the internal registry.
        Called during plugin reload or testing scenarios.

        """
        clear_ingestion_assets()


class DLTIngestionProvider(IngestionProviderPlugin):
    """DLT-based ingestion provider for Phlo.

        Ingestion provider plugin that exposes DLT-based ingestion
    capabilities through the standardized ingestion provider interface.

    Attributes:
            metadata: Static plugin metadata for discovery.

    Methods:
            get_decorator: Return the @phlo_ingestion decorator.
            get_asset_retriever: Return function to get registered assets.

    Example:
            This class is auto-discovered by Phlo:
            ```python
            from phlo_dlt.plugin import DLTIngestionProvider
            provider = DLTIngestionProvider()
            decorator = provider.get_decorator()
            ```

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            PluginMetadata: Static metadata for the DLT ingestion provider.

        """
        return PluginMetadata(
            name="dlt",
            version="0.1.0",
            description="DLT-based ingestion provider with pipeline orchestration",
        )

    def get_decorator(self) -> Callable:
        """Return the @phlo_ingestion decorator.

        Returns:
            Callable: The phlo_ingestion decorator function.

        """
        from phlo_dlt import phlo_ingestion

        return phlo_ingestion

    def get_asset_retriever(self) -> Callable[[], list[Any]]:
        """Return function to get registered ingestion assets.

        Returns:
            Callable[[], list[Any]]: Function that returns list of AssetSpec objects.

        """
        return get_ingestion_assets
