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

    def register_source_connector(
        self, plugin: SourceConnectorPlugin, replace: bool = False
    ) -> None:
        """
        Register a source connector plugin.

        Args:
            plugin: Source connector plugin instance
            replace: Whether to replace existing plugin with same name

        Raises:
            ValueError: If plugin with same name exists and replace=False
        """
        name = plugin.metadata.name

        if name in self._sources and not replace:
            raise ValueError(
                f"Source connector plugin '{name}' is already registered. "
                f"Use replace=True to overwrite."
            )

        self._sources[name] = plugin
        self._all_plugins[f"source:{name}"] = plugin

    def register_quality_check(self, plugin: QualityCheckPlugin, replace: bool = False) -> None:
        """
        Register a quality check plugin.

        Args:
            plugin: Quality check plugin instance
            replace: Whether to replace existing plugin with same name

        Raises:
            ValueError: If plugin with same name exists and replace=False
        """
        name = plugin.metadata.name

        if name in self._quality_checks and not replace:
            raise ValueError(
                f"Quality check plugin '{name}' is already registered. "
                f"Use replace=True to overwrite."
            )

        self._quality_checks[name] = plugin
        self._all_plugins[f"quality:{name}"] = plugin

    def register_transformation(self, plugin: TransformationPlugin, replace: bool = False) -> None:
        """
        Register a transformation plugin.

        Args:
            plugin: Transformation plugin instance
            replace: Whether to replace existing plugin with same name

        Raises:
            ValueError: If plugin with same name exists and replace=False
        """
        name = plugin.metadata.name

        if name in self._transformations and not replace:
            raise ValueError(
                f"Transformation plugin '{name}' is already registered. "
                f"Use replace=True to overwrite."
            )

        self._transformations[name] = plugin
        self._all_plugins[f"transformation:{name}"] = plugin

    def register_service(self, plugin: ServicePlugin, replace: bool = False) -> None:
        """
        Register a service plugin.

        Args:
            plugin: Service plugin instance
            replace: Whether to replace existing plugin with same name

        Raises:
            ValueError: If plugin with same name exists and replace=False
        """
        name = plugin.metadata.name

        if name in self._services and not replace:
            raise ValueError(
                f"Service plugin '{name}' is already registered. Use replace=True to overwrite."
            )

        self._services[name] = plugin
        self._all_plugins[f"service:{name}"] = plugin

    def register_dagster_extension(
        self, plugin: DagsterExtensionPlugin, replace: bool = False
    ) -> None:
        """
        Register a Dagster extension plugin.

        Args:
            plugin: Dagster extension plugin instance
            replace: Whether to replace existing plugin with same name
        """
        name = plugin.metadata.name

        if name in self._dagster_extensions and not replace:
            raise ValueError(
                f"Dagster extension plugin '{name}' is already registered. "
                f"Use replace=True to overwrite."
            )

        self._dagster_extensions[name] = plugin
        self._all_plugins[f"dagster:{name}"] = plugin

    def register_observatory_extension(
        self, plugin: ObservatoryExtensionPlugin, replace: bool = False
    ) -> None:
        """
        Register an Observatory extension plugin.

        Args:
            plugin: Observatory extension plugin instance
            replace: Whether to replace existing plugin with same name
        """
        name = plugin.metadata.name

        if name in self._observatory_extensions and not replace:
            raise ValueError(
                f"Observatory extension plugin '{name}' is already registered. "
                f"Use replace=True to overwrite."
            )

        self._observatory_extensions[name] = plugin
        self._all_plugins[f"observatory:{name}"] = plugin

    def register_cli_command_plugin(self, plugin: CliCommandPlugin, replace: bool = False) -> None:
        """Register a CLI command plugin."""
        name = plugin.metadata.name
        if name in self._cli_commands and not replace:
            raise ValueError(
                f"CLI command plugin '{name}' is already registered. Use replace=True to overwrite."
            )
        self._cli_commands[name] = plugin
        self._all_plugins[f"cli:{name}"] = plugin

    def register_hook_plugin(self, plugin: HookPlugin, replace: bool = False) -> None:
        """Register a hook plugin."""
        name = plugin.metadata.name
        if name in self._hooks and not replace:
            raise ValueError(
                f"Hook plugin '{name}' is already registered. Use replace=True to overwrite."
            )
        self._hooks[name] = plugin
        self._all_plugins[f"hooks:{name}"] = plugin

    def register_asset_provider(self, plugin: AssetProviderPlugin, replace: bool = False) -> None:
        """Register an asset provider plugin."""
        name = plugin.metadata.name
        if name in self._assets and not replace:
            raise ValueError(
                f"Asset provider plugin '{name}' is already registered. Use replace=True to overwrite."
            )
        self._assets[name] = plugin
        self._all_plugins[f"assets:{name}"] = plugin

    def register_resource_provider(
        self, plugin: ResourceProviderPlugin, replace: bool = False
    ) -> None:
        """Register a resource provider plugin."""
        name = plugin.metadata.name
        if name in self._resources and not replace:
            raise ValueError(
                f"Resource provider plugin '{name}' is already registered. Use replace=True to overwrite."
            )
        self._resources[name] = plugin
        self._all_plugins[f"resources:{name}"] = plugin

    def register_orchestrator(
        self, plugin: OrchestratorAdapterPlugin, replace: bool = False
    ) -> None:
        """Register an orchestrator adapter plugin."""
        name = plugin.metadata.name
        if name in self._orchestrators and not replace:
            raise ValueError(
                f"Orchestrator plugin '{name}' is already registered. Use replace=True to overwrite."
            )
        self._orchestrators[name] = plugin
        self._all_plugins[f"orchestrators:{name}"] = plugin

    def register_catalog(self, plugin: CatalogPlugin, replace: bool = False) -> None:
        """
        Register a catalog plugin.

        Args:
            plugin: Catalog plugin instance
            replace: Whether to replace existing plugin with same name

        Raises:
            ValueError: If plugin with same name exists and replace=False
        """
        name = plugin.metadata.name
        if name in self._catalogs and not replace:
            raise ValueError(
                f"Catalog plugin '{name}' is already registered. Use replace=True to overwrite."
            )
        self._catalogs[name] = plugin
        self._all_plugins[f"catalogs:{name}"] = plugin

    def get_source_connector(self, name: str) -> SourceConnectorPlugin | None:
        """
        Get a source connector plugin by name.

        Args:
            name: Plugin name

        Returns:
            SourceConnectorPlugin instance or None if not found
        """
        return self._sources.get(name)

    def get_quality_check(self, name: str) -> QualityCheckPlugin | None:
        """
        Get a quality check plugin by name.

        Args:
            name: Plugin name

        Returns:
            QualityCheckPlugin instance or None if not found
        """
        return self._quality_checks.get(name)

    def get_transformation(self, name: str) -> TransformationPlugin | None:
        """
        Get a transformation plugin by name.

        Args:
            name: Plugin name

        Returns:
            TransformationPlugin instance or None if not found
        """
        return self._transformations.get(name)

    def get_service(self, name: str) -> ServicePlugin | None:
        """
        Get a service plugin by name.

        Args:
            name: Plugin name

        Returns:
            ServicePlugin instance or None if not found
        """
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
        """
        List all registered source connector plugins.

        Returns:
            List of plugin names
        """
        return list(self._sources.keys())

    def list_quality_checks(self) -> list[str]:
        """
        List all registered quality check plugins.

        Returns:
            List of plugin names
        """
        return list(self._quality_checks.keys())

    def list_transformations(self) -> list[str]:
        """
        List all registered transformation plugins.

        Returns:
            List of plugin names
        """
        return list(self._transformations.keys())

    def list_services(self) -> list[str]:
        """
        List all registered service plugins.

        Returns:
            List of plugin names
        """
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
        """
        List all registered plugins by type.

        Returns:
            Dictionary mapping plugin type to list of plugin names
        """
        return {
            "source_connectors": self.list_source_connectors(),
            "quality_checks": self.list_quality_checks(),
            "transformations": self.list_transformations(),
            "services": self.list_services(),
            "dagster_extensions": self.list_dagster_extensions(),
            "observatory_extensions": self.list_observatory_extensions(),
            "cli_commands": self.list_cli_command_plugins(),
            "hooks": self.list_hook_plugins(),
            "asset_providers": self.list_asset_providers(),
            "resource_providers": self.list_resource_providers(),
            "orchestrators": self.list_orchestrators(),
            "catalogs": self.list_catalogs(),
        }

    def clear(self) -> None:
        """Clear all registered plugins."""
        self._sources.clear()
        self._quality_checks.clear()
        self._transformations.clear()
        self._services.clear()
        self._dagster_extensions.clear()
        self._observatory_extensions.clear()
        self._cli_commands.clear()
        self._hooks.clear()
        self._assets.clear()
        self._resources.clear()
        self._orchestrators.clear()
        self._catalogs.clear()
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

    _GETTER_METHODS: dict[str, str] = {
        "source_connectors": "get_source_connector",
        "quality_checks": "get_quality_check",
        "transformations": "get_transformation",
        "services": "get_service",
        "dagster_extensions": "get_dagster_extension",
        "observatory_extensions": "get_observatory_extension",
        "cli_commands": "get_cli_command_plugin",
        "hooks": "get_hook_plugin",
        "catalogs": "get_catalog",
        "asset_providers": "get_asset_provider",
        "resource_providers": "get_resource_provider",
        "orchestrators": "get_orchestrator",
    }

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
        getter_name = self._GETTER_METHODS.get(plugin_type)
        if not getter_name:
            return None
        plugin = getattr(self, getter_name)(name)
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
            if not isinstance(metadata, object):
                return False

            # Check required metadata fields
            required_fields = ["name", "version"]
            for field in required_fields:
                if not hasattr(metadata, field):
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
