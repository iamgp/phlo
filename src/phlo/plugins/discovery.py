"""
Plugin discovery mechanism using Python entry points.

This module discovers and loads plugins from installed Python packages
that declare phlo.plugins entry points.
"""

from __future__ import annotations

import importlib.metadata
import logging
import os

from phlo.plugins.base import (
    Plugin,
    QualityCheckPlugin,
    SourceConnectorPlugin,
    TransformationPlugin,
)
from phlo.plugins.registry import get_global_registry

logger = logging.getLogger(__name__)

# Entry point group names for different plugin types
ENTRY_POINT_GROUPS = {
    "source_connectors": "phlo.plugins.sources",
    "quality_checks": "phlo.plugins.quality",
    "transformations": "phlo.plugins.transforms",
}


def discover_plugins(
    plugin_type: str | None = None, auto_register: bool = True
) -> dict[str, list[Plugin]]:
    """
    Discover all installed Cascade plugins.

    This function scans installed Python packages for phlo.plugins
    entry points and loads the plugins.

    Args:
        plugin_type: Optional plugin type to discover ("source_connectors",
            "quality_checks", "transformations"). If None, discover all types.
        auto_register: If True, automatically register discovered plugins
            in the global registry (default: True)

    Returns:
        Dictionary mapping plugin type to list of discovered plugins

    Example:
        ```python
        # Discover all plugins
        plugins = discover_plugins()
        # {'source_connectors': [...], 'quality_checks': [...], ...}

        # Discover only source connectors
        sources = discover_plugins(plugin_type="source_connectors")
        # {'source_connectors': [...]}
        ```
    """
    discovered: dict[str, list[Plugin]] = {
        "source_connectors": [],
        "quality_checks": [],
        "transformations": [],
    }

    # Determine which plugin types to discover
    types_to_discover = (
        [plugin_type] if plugin_type else list(ENTRY_POINT_GROUPS.keys())
    )

    for ptype in types_to_discover:
        if ptype not in ENTRY_POINT_GROUPS:
            logger.warning(f"Unknown plugin type: {ptype}")
            continue

        entry_point_group = ENTRY_POINT_GROUPS[ptype]

        logger.info(
            f"Discovering {ptype} plugins from entry point: {entry_point_group}"
        )

        # Discover entry points
        try:
            entry_points = importlib.metadata.entry_points(group=entry_point_group)
        except TypeError:
            # Python 3.9 compatibility - entry_points() returns dict
            all_entry_points = importlib.metadata.entry_points()
            entry_points = all_entry_points.get(entry_point_group, [])

        # Load each plugin
        for entry_point in entry_points:
            try:
                logger.info(
                    f"Loading plugin: {entry_point.name} from {entry_point.value}"
                )

                # Load the plugin class
                plugin_class = entry_point.load()

                # Instantiate the plugin
                if isinstance(plugin_class, type):
                    # It's a class, instantiate it
                    plugin = plugin_class()
                else:
                    # It's already an instance
                    plugin = plugin_class

                # Validate plugin type
                if not isinstance(plugin, Plugin):
                    logger.error(
                        f"Plugin {entry_point.name} does not inherit from Plugin base class"
                    )
                    continue

                # Validate specific plugin type
                expected_type = {
                    "source_connectors": SourceConnectorPlugin,
                    "quality_checks": QualityCheckPlugin,
                    "transformations": TransformationPlugin,
                }[ptype]

                if not isinstance(plugin, expected_type):
                    logger.error(
                        f"Plugin {entry_point.name} has incorrect type. "
                        f"Expected {expected_type.__name__}, got {type(plugin).__name__}"
                    )
                    continue

                # Add to discovered plugins
                discovered[ptype].append(plugin)

                logger.info(
                    f"Successfully loaded plugin: {plugin.metadata.name} "
                    f"v{plugin.metadata.version}"
                )

                # Auto-register if requested
                if auto_register:
                    registry = get_global_registry()
                    if ptype == "source_connectors":
                        registry.register_source_connector(plugin, replace=True)
                    elif ptype == "quality_checks":
                        registry.register_quality_check(plugin, replace=True)
                    elif ptype == "transformations":
                        registry.register_transformation(plugin, replace=True)

            except Exception as exc:
                logger.error(
                    f"Failed to load plugin {entry_point.name}: {exc}", exc_info=True
                )
                continue

    # Log summary
    total = sum(len(plugins) for plugins in discovered.values())
    logger.info(f"Discovered {total} plugins: {discovered}")

    return discovered


def list_plugins(plugin_type: str | None = None) -> dict[str, list[str]]:
    """
    List all plugins in the global registry.

    Args:
        plugin_type: Optional plugin type to list ("source_connectors",
            "quality_checks", "transformations"). If None, list all types.

    Returns:
        Dictionary mapping plugin type to list of plugin names

    Example:
        ```python
        # List all plugins
        all_plugins = list_plugins()
        # {'source_connectors': ['github', 'weather_api'], ...}

        # List only source connectors
        sources = list_plugins(plugin_type="source_connectors")
        # {'source_connectors': ['github', 'weather_api']}
        ```
    """
    registry = get_global_registry()
    all_plugins = registry.list_all_plugins()

    if plugin_type:
        if plugin_type not in all_plugins:
            return {plugin_type: []}
        return {plugin_type: all_plugins[plugin_type]}

    return all_plugins


def get_plugin(plugin_type: str, name: str) -> Plugin | None:
    """
    Get a plugin by type and name.

    Args:
        plugin_type: Plugin type ("source_connectors", "quality_checks", "transformations")
        name: Plugin name

    Returns:
        Plugin instance or None if not found

    Example:
        ```python
        plugin = get_plugin("source_connectors", "github")
        if plugin:
            data = plugin.fetch_data(config={...})
        ```
    """
    registry = get_global_registry()

    if plugin_type == "source_connectors":
        return registry.get_source_connector(name)
    elif plugin_type == "quality_checks":
        return registry.get_quality_check(name)
    elif plugin_type == "transformations":
        return registry.get_transformation(name)
    else:
        logger.warning(f"Unknown plugin type: {plugin_type}")
        return None


def get_source_connector(name: str) -> SourceConnectorPlugin | None:
    """
    Get a source connector plugin by name.

    Args:
        name: Plugin name

    Returns:
        SourceConnectorPlugin instance or None if not found

    Example:
        ```python
        github = get_source_connector("github")
        if github:
            events = github.fetch_data(config={"repo": "owner/repo"})
        ```
    """
    registry = get_global_registry()
    return registry.get_source_connector(name)


def get_quality_check(name: str) -> QualityCheckPlugin | None:
    """
    Get a quality check plugin by name.

    Args:
        name: Plugin name

    Returns:
        QualityCheckPlugin instance or None if not found

    Example:
        ```python
        custom_check = get_quality_check("business_rule")
        if custom_check:
            check = custom_check.create_check(rule="revenue > 0")
        ```
    """
    registry = get_global_registry()
    return registry.get_quality_check(name)


def get_transformation(name: str) -> TransformationPlugin | None:
    """
    Get a transformation plugin by name.

    Args:
        name: Plugin name

    Returns:
        TransformationPlugin instance or None if not found

    Example:
        ```python
        pivot = get_transformation("pivot")
        if pivot:
            result = pivot.transform(df, config={"index": "date", ...})
        ```
    """
    registry = get_global_registry()
    return registry.get_transformation(name)


def auto_discover() -> None:
    """
    Automatically discover and register all plugins on import.

    This function is called automatically when phlo is imported.
    It discovers all installed plugins and registers them in the
    global registry.
    """
    try:
        discover_plugins(auto_register=True)
    except Exception as exc:
        logger.warning(f"Failed to auto-discover plugins: {exc}")


# Auto-discover plugins when module is imported
# This ensures plugins are available immediately after import
# Users can disable this by setting CASCADE_NO_AUTO_DISCOVER env var
if not os.environ.get("CASCADE_NO_AUTO_DISCOVER"):
    try:
        auto_discover()
    except Exception:
        # Silently fail on auto-discovery to not break import
        pass
