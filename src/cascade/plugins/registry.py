"""
Plugin registry for managing loaded plugins.

The registry maintains a catalog of discovered plugins and provides
methods for accessing them by name and type.
"""

from __future__ import annotations

from cascade.plugins.base import (
    Plugin,
    QualityCheckPlugin,
    SourceConnectorPlugin,
    TransformationPlugin,
)


class PluginRegistry:
    """
    Central registry for Cascade plugins.

    The registry maintains separate catalogs for each plugin type
    and provides methods for registering and retrieving plugins.
    """

    def __init__(self):
        """Initialize empty plugin registry."""
        self._sources: dict[str, SourceConnectorPlugin] = {}
        self._quality_checks: dict[str, QualityCheckPlugin] = {}
        self._transformations: dict[str, TransformationPlugin] = {}
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

    def register_quality_check(
        self, plugin: QualityCheckPlugin, replace: bool = False
    ) -> None:
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

    def register_transformation(
        self, plugin: TransformationPlugin, replace: bool = False
    ) -> None:
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
        }

    def clear(self) -> None:
        """Clear all registered plugins."""
        self._sources.clear()
        self._quality_checks.clear()
        self._transformations.clear()
        self._all_plugins.clear()

    def __len__(self) -> int:
        """Return total number of registered plugins."""
        return len(self._all_plugins)

    def __contains__(self, key: str) -> bool:
        """Check if a plugin is registered (key format: 'type:name')."""
        return key in self._all_plugins


# Global registry instance
_global_registry = PluginRegistry()


def get_global_registry() -> PluginRegistry:
    """
    Get the global plugin registry instance.

    Returns:
        Global PluginRegistry instance
    """
    return _global_registry
