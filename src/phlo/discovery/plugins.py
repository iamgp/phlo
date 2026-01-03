"""
Plugin discovery mechanism using Python entry points.

This module discovers and loads plugins from installed Python packages
that declare phlo.plugins entry points.
"""

from __future__ import annotations

import importlib.metadata
import os

from phlo.config import get_settings
from phlo.discovery.registry import get_global_registry
from phlo.logging import get_logger, suppress_log_routing
from phlo.plugins.base import (
    AssetProviderPlugin,
    CliCommandPlugin,
    DagsterExtensionPlugin,
    OrchestratorAdapterPlugin,
    Plugin,
    QualityCheckPlugin,
    ResourceProviderPlugin,
    ServicePlugin,
    SourceConnectorPlugin,
    TransformationPlugin,
    TrinoCatalogPlugin,
)
from phlo.plugins.hooks import HookPlugin

logger = get_logger(__name__)

# Entry point group names for different plugin types
ENTRY_POINT_GROUPS = {
    "source_connectors": "phlo.plugins.sources",
    "quality_checks": "phlo.plugins.quality",
    "transformations": "phlo.plugins.transforms",
    "services": "phlo.plugins.services",
    "dagster_extensions": "phlo.plugins.dagster",
    "cli_commands": "phlo.plugins.cli",
    "hooks": "phlo.plugins.hooks",
    "trino_catalogs": "phlo.plugins.trino_catalogs",
    "asset_providers": "phlo.plugins.assets",
    "resource_providers": "phlo.plugins.resources",
    "orchestrators": "phlo.plugins.orchestrators",
}


def _is_plugin_allowed(plugin_name: str) -> bool:
    """
    Check if a plugin is allowed based on whitelist/blacklist configuration.

    Args:
        plugin_name: Name of the plugin

    Returns:
        True if plugin should be loaded, False otherwise
    """
    settings = get_settings()

    # Check blacklist first
    if plugin_name in settings.plugins_blacklist:
        logger.debug(f"Plugin '{plugin_name}' is blacklisted, skipping")
        return False

    # Check whitelist (if not empty)
    if settings.plugins_whitelist and plugin_name not in settings.plugins_whitelist:
        logger.debug(f"Plugin '{plugin_name}' is not in whitelist, skipping")
        return False

    return True


def discover_plugins(
    plugin_type: str | None = None, auto_register: bool = True
) -> dict[str, list[Plugin]]:
    """
    Discover all installed Phlo plugins.

    This function scans installed Python packages for phlo.plugins
    entry points and loads the plugins.

    Args:
        plugin_type: Optional plugin type to discover ("source_connectors",
            "quality_checks", "transformations", "services"). If None, discover all types.
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
    settings = get_settings()

    with suppress_log_routing():
        # Check if plugins are enabled
        if not settings.plugins_enabled:
            logger.info("Plugin system is disabled")
            return {
                "source_connectors": [],
                "quality_checks": [],
                "transformations": [],
                "services": [],
                "dagster_extensions": [],
                "cli_commands": [],
                "hooks": [],
                "trino_catalogs": [],
                "asset_providers": [],
                "resource_providers": [],
                "orchestrators": [],
            }

        discovered: dict[str, list[Plugin]] = {
            "source_connectors": [],
            "quality_checks": [],
            "transformations": [],
            "services": [],
            "dagster_extensions": [],
            "cli_commands": [],
            "hooks": [],
            "trino_catalogs": [],
            "asset_providers": [],
            "resource_providers": [],
            "orchestrators": [],
        }

        # Determine which plugin types to discover
        types_to_discover = [plugin_type] if plugin_type else list(ENTRY_POINT_GROUPS.keys())

        for ptype in types_to_discover:
            if ptype not in ENTRY_POINT_GROUPS:
                logger.warning(f"Unknown plugin type: {ptype}")
                continue

            entry_point_group = ENTRY_POINT_GROUPS[ptype]

            logger.info(f"Discovering {ptype} plugins from entry point: {entry_point_group}")

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
                    # Check if plugin is allowed
                    if not _is_plugin_allowed(entry_point.name):
                        continue

                    logger.info(f"Loading plugin: {entry_point.name} from {entry_point.value}")

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
                        "services": ServicePlugin,
                        "dagster_extensions": DagsterExtensionPlugin,
                        "cli_commands": CliCommandPlugin,
                        "hooks": HookPlugin,
                        "trino_catalogs": TrinoCatalogPlugin,
                        "asset_providers": AssetProviderPlugin,
                        "resource_providers": ResourceProviderPlugin,
                        "orchestrators": OrchestratorAdapterPlugin,
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
                        f"Successfully loaded plugin: {plugin.metadata.name} v{plugin.metadata.version}"
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
                        elif ptype == "services":
                            registry.register_service(plugin, replace=True)
                        elif ptype == "dagster_extensions":
                            registry.register_dagster_extension(plugin, replace=True)
                        elif ptype == "cli_commands":
                            registry.register_cli_command_plugin(plugin, replace=True)
                        elif ptype == "hooks":
                            registry.register_hook_plugin(plugin, replace=True)
                        elif ptype == "trino_catalogs":
                            pass  # Trino catalogs are used directly, not registry-based
                        elif ptype == "asset_providers":
                            registry.register_asset_provider(plugin, replace=True)
                        elif ptype == "resource_providers":
                            registry.register_resource_provider(plugin, replace=True)
                        elif ptype == "orchestrators":
                            registry.register_orchestrator(plugin, replace=True)

                except Exception as exc:
                    logger.error(
                        f"Failed to load plugin {entry_point.name}: {exc}",
                        exc_info=True,
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
            "quality_checks", "transformations", "services"). If None, list all types.

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
        plugin_type: Plugin type ("source_connectors", "quality_checks", "transformations",
        "services", "dagster_extensions", "cli_commands", "hooks", "asset_providers",
        "resource_providers", "orchestrators")
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
    elif plugin_type == "services":
        return registry.get_service(name)
    elif plugin_type == "dagster_extensions":
        return registry.get_dagster_extension(name)
    elif plugin_type == "cli_commands":
        return registry.get_cli_command_plugin(name)
    elif plugin_type == "hooks":
        return registry.get_hook_plugin(name)
    elif plugin_type == "asset_providers":
        return registry.get_asset_provider(name)
    elif plugin_type == "resource_providers":
        return registry.get_resource_provider(name)
    elif plugin_type == "orchestrators":
        return registry.get_orchestrator(name)
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


def get_service(name: str) -> ServicePlugin | None:
    """
    Get a service plugin by name.

    Args:
        name: Plugin name

    Returns:
        ServicePlugin instance or None if not found
    """
    registry = get_global_registry()
    return registry.get_service(name)


def get_hook_plugin(name: str) -> HookPlugin | None:
    """
    Get a hook plugin by name.

    Args:
        name: Plugin name

    Returns:
        HookPlugin instance or None if not found
    """
    registry = get_global_registry()
    return registry.get_hook_plugin(name)


def get_plugin_info(plugin_type: str, name: str) -> dict | None:
    """
    Get detailed information about a plugin.

    Args:
        plugin_type: Plugin type ("source_connectors", "quality_checks", "transformations",
            "services", "dagster_extensions", "cli_commands", "hooks")
        name: Plugin name

    Returns:
        Dictionary with plugin information or None if not found

    Example:
        ```python
        info = get_plugin_info("source_connectors", "github")
        if info:
            version = info["version"]
            author = info["author"]
        ```
    """
    registry = get_global_registry()
    return registry.get_plugin_metadata(plugin_type, name)


def validate_plugins() -> dict[str, list[str]]:
    """
    Validate all registered plugins.

    Checks that all plugins comply with their interface requirements.

    Returns:
        Dictionary with two keys:
        - 'valid': List of valid plugin names
        - 'invalid': List of invalid plugin names
    """
    registry = get_global_registry()
    all_plugins = registry.list_all_plugins()

    valid = []
    invalid = []

    for plugin_type, plugin_names in all_plugins.items():
        for name in plugin_names:
            plugin = None
            if plugin_type == "source_connectors":
                plugin = registry.get_source_connector(name)
            elif plugin_type == "quality_checks":
                plugin = registry.get_quality_check(name)
            elif plugin_type == "transformations":
                plugin = registry.get_transformation(name)
            elif plugin_type == "services":
                plugin = registry.get_service(name)
            elif plugin_type == "dagster_extensions":
                plugin = registry.get_dagster_extension(name)
            elif plugin_type == "cli_commands":
                plugin = registry.get_cli_command_plugin(name)
            elif plugin_type == "hooks":
                plugin = registry.get_hook_plugin(name)
            elif plugin_type == "asset_providers":
                plugin = registry.get_asset_provider(name)
            elif plugin_type == "resource_providers":
                plugin = registry.get_resource_provider(name)
            elif plugin_type == "orchestrators":
                plugin = registry.get_orchestrator(name)

            if plugin and registry.validate_plugin(plugin):
                valid.append(f"{plugin_type}:{name}")
            else:
                invalid.append(f"{plugin_type}:{name}")

    return {"valid": valid, "invalid": invalid}


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
# Users can disable this by setting PHLO_NO_AUTO_DISCOVER env var
if not os.environ.get("PHLO_NO_AUTO_DISCOVER"):
    try:
        auto_discover()
    except Exception:
        # Silently fail on auto-discovery to not break import
        pass
