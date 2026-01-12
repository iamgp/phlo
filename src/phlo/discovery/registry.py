"""
Plugin registry for managing loaded plugins.

The registry maintains a catalog of discovered plugins and provides
methods for accessing them by name and type.
"""

from __future__ import annotations

from phlo.plugins.base import (
    AssetProviderPlugin,
    CatalogPlugin,
    CliCommandPlugin,
    DagsterExtensionPlugin,
    ObservatoryExtensionPlugin,
    OrchestratorAdapterPlugin,
    Plugin,
    QualityCheckPlugin,
    ResourceProviderPlugin,
    ServicePlugin,
    SourceConnectorPlugin,
    TransformationPlugin,
)
from phlo.plugins.hooks import HookPlugin

_TYPE_CONFIG = {
    "source_connectors": ("_sources", "source", "Source connector"),
    "quality_checks": ("_quality_checks", "quality", "Quality check"),
    "transformations": ("_transformations", "transformation", "Transformation"),
    "services": ("_services", "service", "Service"),
    "dagster_extensions": ("_dagster_extensions", "dagster", "Dagster extension"),
    "observatory_extensions": ("_observatory_extensions", "observatory", "Observatory extension"),
    "cli_commands": ("_cli_commands", "cli", "CLI command"),
    "hooks": ("_hooks", "hooks", "Hook"),
    "asset_providers": ("_assets", "assets", "Asset provider"),
    "resource_providers": ("_resources", "resources", "Resource provider"),
    "orchestrators": ("_orchestrators", "orchestrators", "Orchestrator"),
    "catalogs": ("_catalogs", "catalogs", "Catalog"),
}


class PluginRegistry:
    """
    Central registry for Phlo plugins.

    The registry maintains separate catalogs for each plugin type
    and provides methods for registering and retrieving plugins.
    """

    def __init__(self):
        """Initialize empty plugin registry."""
        self._sources: dict[str, SourceConnectorPlugin] = {}
        self._quality_checks: dict[str, QualityCheckPlugin] = {}
        self._transformations: dict[str, TransformationPlugin] = {}
        self._services: dict[str, ServicePlugin] = {}
        self._dagster_extensions: dict[str, DagsterExtensionPlugin] = {}
        self._observatory_extensions: dict[str, ObservatoryExtensionPlugin] = {}
        self._cli_commands: dict[str, CliCommandPlugin] = {}
        self._hooks: dict[str, HookPlugin] = {}
        self._assets: dict[str, AssetProviderPlugin] = {}
        self._resources: dict[str, ResourceProviderPlugin] = {}
        self._orchestrators: dict[str, OrchestratorAdapterPlugin] = {}
        self._catalogs: dict[str, CatalogPlugin] = {}
        self._all_plugins: dict[str, Plugin] = {}

    def _register_plugin(self, plugin_type: str, plugin: Plugin, replace: bool = False) -> None:
        """Register a plugin of any type."""
        config = _TYPE_CONFIG.get(plugin_type)
        if not config:
            raise ValueError(f"Unknown plugin type: {plugin_type}")

        dict_name, key_prefix, type_label = config
        plugin_dict = getattr(self, dict_name)
        name = plugin.metadata.name

        if name in plugin_dict and not replace:
            raise ValueError(
                f"{type_label} plugin '{name}' is already registered. "
                f"Use replace=True to overwrite."
            )

        plugin_dict[name] = plugin
        self._all_plugins[f"{key_prefix}:{name}"] = plugin

    def register_source_connector(
        self, plugin: SourceConnectorPlugin, replace: bool = False
    ) -> None:
        """Register a source connector plugin."""
        self._register_plugin("source_connectors", plugin, replace)

    def register_quality_check(self, plugin: QualityCheckPlugin, replace: bool = False) -> None:
        """Register a quality check plugin."""
        self._register_plugin("quality_checks", plugin, replace)

    def register_transformation(self, plugin: TransformationPlugin, replace: bool = False) -> None:
        """Register a transformation plugin."""
        self._register_plugin("transformations", plugin, replace)

    def register_service(self, plugin: ServicePlugin, replace: bool = False) -> None:
        """Register a service plugin."""
        self._register_plugin("services", plugin, replace)

    def register_dagster_extension(
        self, plugin: DagsterExtensionPlugin, replace: bool = False
    ) -> None:
        """Register a Dagster extension plugin."""
        self._register_plugin("dagster_extensions", plugin, replace)

    def register_observatory_extension(
        self, plugin: ObservatoryExtensionPlugin, replace: bool = False
    ) -> None:
        """Register an Observatory extension plugin."""
        self._register_plugin("observatory_extensions", plugin, replace)

    def register_cli_command_plugin(self, plugin: CliCommandPlugin, replace: bool = False) -> None:
        """Register a CLI command plugin."""
        self._register_plugin("cli_commands", plugin, replace)

    def register_hook_plugin(self, plugin: HookPlugin, replace: bool = False) -> None:
        """Register a hook plugin."""
        self._register_plugin("hooks", plugin, replace)

    def register_asset_provider(self, plugin: AssetProviderPlugin, replace: bool = False) -> None:
        """Register an asset provider plugin."""
        self._register_plugin("asset_providers", plugin, replace)

    def register_resource_provider(
        self, plugin: ResourceProviderPlugin, replace: bool = False
    ) -> None:
        """Register a resource provider plugin."""
        self._register_plugin("resource_providers", plugin, replace)

    def register_orchestrator(
        self, plugin: OrchestratorAdapterPlugin, replace: bool = False
    ) -> None:
        """Register an orchestrator adapter plugin."""
        self._register_plugin("orchestrators", plugin, replace)

    def register_catalog(self, plugin: CatalogPlugin, replace: bool = False) -> None:
        """Register a catalog plugin."""
        self._register_plugin("catalogs", plugin, replace)

    def get(self, plugin_type: str, name: str) -> Plugin | None:
        """Get a plugin by type and name."""
        config = _TYPE_CONFIG.get(plugin_type)
        if not config:
            return None
        return getattr(self, config[0]).get(name)

    def list(self, plugin_type: str) -> list[str]:
        """List all plugins of a given type."""
        config = _TYPE_CONFIG.get(plugin_type)
        if not config:
            return []
        return list(getattr(self, config[0]).keys())

    def register(self, plugin_type: str, plugin: Plugin, replace: bool = False) -> None:
        """Register a plugin of any type (alias for _register_plugin)."""
        self._register_plugin(plugin_type, plugin, replace)

    def get_source_connector(self, name: str) -> SourceConnectorPlugin | None:
        """Get a source connector plugin by name."""
        return self._sources.get(name)

    def get_quality_check(self, name: str) -> QualityCheckPlugin | None:
        """Get a quality check plugin by name."""
        return self._quality_checks.get(name)

    def get_transformation(self, name: str) -> TransformationPlugin | None:
        """Get a transformation plugin by name."""
        return self._transformations.get(name)

    def get_service(self, name: str) -> ServicePlugin | None:
        """Get a service plugin by name."""
        return self._services.get(name)

    def get_dagster_extension(self, name: str) -> DagsterExtensionPlugin | None:
        """Get a Dagster extension plugin by name."""
        return self._dagster_extensions.get(name)

    def get_observatory_extension(self, name: str) -> ObservatoryExtensionPlugin | None:
        """Get an Observatory extension plugin by name."""
        return self._observatory_extensions.get(name)

    def get_cli_command_plugin(self, name: str) -> CliCommandPlugin | None:
        """Get a CLI command plugin by name."""
        return self._cli_commands.get(name)

    def get_hook_plugin(self, name: str) -> HookPlugin | None:
        """Get a hook plugin by name."""
        return self._hooks.get(name)

    def get_asset_provider(self, name: str) -> AssetProviderPlugin | None:
        """Get an asset provider plugin by name."""
        return self._assets.get(name)

    def get_resource_provider(self, name: str) -> ResourceProviderPlugin | None:
        """Get a resource provider plugin by name."""
        return self._resources.get(name)

    def get_orchestrator(self, name: str) -> OrchestratorAdapterPlugin | None:
        """Get an orchestrator adapter plugin by name."""
        return self._orchestrators.get(name)

    def get_catalog(self, name: str) -> CatalogPlugin | None:
        """Get a catalog plugin by name."""
        return self._catalogs.get(name)

    def list_source_connectors(self) -> list[str]:
        """List all registered source connector plugins."""
        return list(self._sources.keys())

    def list_quality_checks(self) -> list[str]:
        """List all registered quality check plugins."""
        return list(self._quality_checks.keys())

    def list_transformations(self) -> list[str]:
        """List all registered transformation plugins."""
        return list(self._transformations.keys())

    def list_services(self) -> list[str]:
        """List all registered service plugins."""
        return list(self._services.keys())

    def list_dagster_extensions(self) -> list[str]:
        """List all registered Dagster extension plugins."""
        return list(self._dagster_extensions.keys())

    def list_observatory_extensions(self) -> list[str]:
        """List all registered Observatory extension plugins."""
        return list(self._observatory_extensions.keys())

    def list_cli_command_plugins(self) -> list[str]:
        """List all registered CLI command plugins."""
        return list(self._cli_commands.keys())

    def list_hook_plugins(self) -> list[str]:
        """List all registered hook plugins."""
        return list(self._hooks.keys())

    def list_asset_providers(self) -> list[str]:
        """List all registered asset provider plugins."""
        return list(self._assets.keys())

    def list_resource_providers(self) -> list[str]:
        """List all registered resource provider plugins."""
        return list(self._resources.keys())

    def list_orchestrators(self) -> list[str]:
        """List all registered orchestrator adapter plugins."""
        return list(self._orchestrators.keys())

    def list_catalogs(self) -> list[str]:
        """List all registered catalog plugins."""
        return list(self._catalogs.keys())

    def list_all_plugins(self) -> dict[str, list[str]]:
        """List all registered plugins by type."""
        return {ptype: self.list(ptype) for ptype in _TYPE_CONFIG}

    def clear(self) -> None:
        """Clear all registered plugins."""
        for config in _TYPE_CONFIG.values():
            getattr(self, config[0]).clear()
        self._all_plugins.clear()

    def iter_plugins(self) -> list[Plugin]:
        """Return all registered plugin instances."""
        return list(self._all_plugins.values())

    def __len__(self) -> int:
        """Return total number of registered plugins."""
        return len(self._all_plugins)

    def __contains__(self, key: str) -> bool:
        """Check if a plugin is registered (key format: 'type:name')."""
        return key in self._all_plugins

    def get_plugin_metadata(self, plugin_type: str, name: str) -> dict | None:
        """
        Get metadata for a plugin by type and name.

        Args:
            plugin_type: Plugin type ("source_connectors", "quality_checks", "transformations",
                "services", "catalogs")
            name: Plugin name

        Returns:
            Dictionary with plugin metadata or None if not found
        """
        plugin = self.get(plugin_type, name)
        if not plugin:
            return None

        metadata = plugin.metadata
        return {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "author": metadata.author,
            "license": metadata.license,
            "homepage": metadata.homepage,
            "tags": metadata.tags,
            "dependencies": metadata.dependencies,
        }

    def validate_plugin(self, plugin: Plugin) -> bool:
        """
        Validate plugin interface compliance.

        Args:
            plugin: Plugin instance to validate

        Returns:
            True if plugin is valid, False otherwise
        """
        # Check required attributes
        if not hasattr(plugin, "metadata"):
            return False

        try:
            metadata = plugin.metadata
            # Check required metadata fields
            if not all(hasattr(metadata, f) for f in ("name", "version")):
                return False
        except Exception:
            return False

        # Type-specific validation
        if isinstance(plugin, SourceConnectorPlugin):
            return hasattr(plugin, "fetch_data") and callable(plugin.fetch_data)
        elif isinstance(plugin, QualityCheckPlugin):
            return hasattr(plugin, "create_check") and callable(plugin.create_check)
        elif isinstance(plugin, TransformationPlugin):
            return hasattr(plugin, "transform") and callable(plugin.transform)
        elif isinstance(plugin, ServicePlugin):
            try:
                service_definition = plugin.service_definition
            except Exception:
                return False
            return isinstance(service_definition, dict)
        elif isinstance(plugin, HookPlugin):
            return hasattr(plugin, "get_hooks") and callable(plugin.get_hooks)
        elif isinstance(plugin, AssetProviderPlugin):
            return hasattr(plugin, "get_assets") and callable(plugin.get_assets)
        elif isinstance(plugin, ResourceProviderPlugin):
            return hasattr(plugin, "get_resources") and callable(plugin.get_resources)
        elif isinstance(plugin, OrchestratorAdapterPlugin):
            return hasattr(plugin, "build_definitions") and callable(plugin.build_definitions)
        elif isinstance(plugin, CatalogPlugin):
            has_catalog = hasattr(plugin, "catalog_name")
            has_targets = hasattr(plugin, "targets")
            has_properties = hasattr(plugin, "get_properties") and callable(plugin.get_properties)
            return has_catalog and has_targets and has_properties
        elif isinstance(plugin, ObservatoryExtensionPlugin):
            has_manifest = hasattr(plugin, "manifest")
            has_asset_root = hasattr(plugin, "asset_root")
            return has_manifest and has_asset_root

        return True


# Global registry instance
_global_registry = PluginRegistry()


def get_global_registry() -> PluginRegistry:
    """
    Get the global plugin registry instance.

    Returns:
        Global PluginRegistry instance
    """
    return _global_registry
