"""
Plugin registry for managing loaded plugins.

The registry maintains a catalog of discovered plugins and provides
methods for accessing them by name and type.
"""

from __future__ import annotations

from phlo.plugins.base import (
    CliCommandPlugin,
    DagsterExtensionPlugin,
    Plugin,
    QualityCheckPlugin,
    ServicePlugin,
    SourceConnectorPlugin,
    TransformationPlugin,
)


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
        self._cli_commands: dict[str, CliCommandPlugin] = {}
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

    def register_cli_command_plugin(self, plugin: CliCommandPlugin, replace: bool = False) -> None:
        """Register a CLI command plugin."""
        name = plugin.metadata.name
        if name in self._cli_commands and not replace:
            raise ValueError(
                f"CLI command plugin '{name}' is already registered. Use replace=True to overwrite."
            )
        self._cli_commands[name] = plugin
        self._all_plugins[f"cli:{name}"] = plugin

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

    def get_cli_command_plugin(self, name: str) -> CliCommandPlugin | None:
        """Get a CLI command plugin by name."""
        return self._cli_commands.get(name)

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

    def list_cli_command_plugins(self) -> list[str]:
        """List all registered CLI command plugins."""
        return list(self._cli_commands.keys())

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
            "cli_commands": self.list_cli_command_plugins(),
        }

    def clear(self) -> None:
        """Clear all registered plugins."""
        self._sources.clear()
        self._quality_checks.clear()
        self._transformations.clear()
        self._services.clear()
        self._dagster_extensions.clear()
        self._cli_commands.clear()
        self._all_plugins.clear()

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
                "services")
            name: Plugin name

        Returns:
            Dictionary with plugin metadata or None if not found
        """
        plugin = None
        if plugin_type == "source_connectors":
            plugin = self.get_source_connector(name)
        elif plugin_type == "quality_checks":
            plugin = self.get_quality_check(name)
        elif plugin_type == "transformations":
            plugin = self.get_transformation(name)
        elif plugin_type == "services":
            plugin = self.get_service(name)

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
