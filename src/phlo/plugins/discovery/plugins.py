"""
Plugin discovery mechanism using Python entry points.

This module discovers and loads plugins from installed Python packages
that declare phlo.plugins entry points.
"""

from __future__ import annotations

import importlib.metadata
import os

from phlo.config import get_settings
from phlo.logging import get_logger, suppress_log_routing
from phlo.plugins.base import (
    AssetProviderPlugin,
    CatalogPlugin,
    CliCommandPlugin,
    OrchestratorAdapterPlugin,
    Plugin,
    QualityCheckPlugin,
    ResourceProviderPlugin,
    ServicePlugin,
    SourceConnectorPlugin,
    TransformationPlugin,
)
from phlo.plugins.discovery.registry import get_global_registry
from phlo.plugins.hooks import HookPlugin

logger = get_logger(__name__)

_NO_AUTO_DISCOVER_ENV = "PHLO_NO_AUTO_DISCOVER"
_TRUTHY_ENV_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSY_ENV_VALUES = frozenset({"0", "false", "no", "off", ""})

# Entry point group names for different plugin types
ENTRY_POINT_GROUPS = {
    "source_connectors": "phlo.plugins.sources",
    "quality_checks": "phlo.plugins.quality",
    "transformations": "phlo.plugins.transforms",
    "services": "phlo.plugins.services",
    "cli_commands": "phlo.plugins.cli",
    "hooks": "phlo.plugins.hooks",
    "catalogs": "phlo.plugins.catalogs",
    "asset_providers": "phlo.plugins.assets",
    "resource_providers": "phlo.plugins.resources",
    "orchestrators": "phlo.plugins.orchestrators",
}

# Maps plugin type to registry registration method name
_PLUGIN_REGISTER_METHODS = {
    "source_connectors": "register_source_connector",
    "quality_checks": "register_quality_check",
    "transformations": "register_transformation",
    "services": "register_service",
    "cli_commands": "register_cli_command_plugin",
    "hooks": "register_hook_plugin",
    "catalogs": "register_catalog",
    "asset_providers": "register_asset_provider",
    "resource_providers": "register_resource_provider",
    "orchestrators": "register_orchestrator",
}

# Maps plugin type to registry getter method name
_PLUGIN_GETTER_METHODS = {
    "source_connectors": "get_source_connector",
    "quality_checks": "get_quality_check",
    "transformations": "get_transformation",
    "services": "get_service",
    "cli_commands": "get_cli_command_plugin",
    "hooks": "get_hook_plugin",
    "catalogs": "get_catalog",
    "asset_providers": "get_asset_provider",
    "resource_providers": "get_resource_provider",
    "orchestrators": "get_orchestrator",
}

_PLUGIN_EXPECTED_TYPES = {
    "source_connectors": SourceConnectorPlugin,
    "quality_checks": QualityCheckPlugin,
    "transformations": TransformationPlugin,
    "services": ServicePlugin,
    "cli_commands": CliCommandPlugin,
    "hooks": HookPlugin,
    "catalogs": CatalogPlugin,
    "asset_providers": AssetProviderPlugin,
    "resource_providers": ResourceProviderPlugin,
    "orchestrators": OrchestratorAdapterPlugin,
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
        logger.debug("plugin_blacklisted_skipping", plugin_name=plugin_name)
        return False

    # Check whitelist (if not empty)
    if settings.plugins_whitelist and plugin_name not in settings.plugins_whitelist:
        logger.debug("plugin_not_whitelisted_skipping", plugin_name=plugin_name)
        return False

    return True


def _register_plugin_with_lifecycle(plugin_type: str, plugin: Plugin, replace: bool = True) -> None:
    """Register plugin with initialize/cleanup lifecycle hooks and rollback safeguards."""
    registry = get_global_registry()
    register_method_name = _PLUGIN_REGISTER_METHODS.get(plugin_type)
    getter_method_name = _PLUGIN_GETTER_METHODS.get(plugin_type)

    if not register_method_name or not getter_method_name:
        raise ValueError(f"Unknown plugin type: {plugin_type}")

    register_method = getattr(registry, register_method_name)
    existing_plugin = getattr(registry, getter_method_name)(plugin.metadata.name)

    # Let registry raise duplicate registration errors without initializing a plugin that
    # cannot be registered.
    if existing_plugin and not replace:
        register_method(plugin, replace=False)
        return

    try:
        plugin.initialize({})
    except Exception:
        try:
            plugin.cleanup()
        except Exception:
            logger.warning(
                "plugin_cleanup_after_initialize_failed",
                plugin_type=plugin_type,
                plugin_name=plugin.metadata.name,
                exc_info=True,
            )
        raise

    existing_cleaned = False
    try:
        if existing_plugin and replace:
            existing_plugin.cleanup()
            existing_cleaned = True
        register_method(plugin, replace=replace)
    except Exception:
        if existing_cleaned:
            try:
                existing_plugin.initialize({})
            except Exception:
                logger.error(
                    "plugin_recovery_initialize_failed",
                    plugin_type=plugin_type,
                    plugin_name=plugin.metadata.name,
                    exc_info=True,
                )
        try:
            plugin.cleanup()
        except Exception:
            logger.warning(
                "plugin_cleanup_after_registration_failed",
                plugin_type=plugin_type,
                plugin_name=plugin.metadata.name,
                exc_info=True,
            )
        raise


def discover_plugins(
    plugin_type: str | None = None, auto_register: bool = True
) -> dict[str, list[Plugin]]:
    """
    Discover all installed Phlo plugins.

    This function scans installed Python packages for phlo.plugins
    entry points and loads the plugins.

    Args:
        plugin_type: Optional plugin type to discover ("source_connectors",
            "quality_checks", "transformations", "services", "catalogs"). If None, discover all types.
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
            return {k: [] for k in ENTRY_POINT_GROUPS}

        discovered: dict[str, list[Plugin]] = {k: [] for k in ENTRY_POINT_GROUPS}

        # Determine which plugin types to discover
        types_to_discover = [plugin_type] if plugin_type else list(ENTRY_POINT_GROUPS.keys())

        for ptype in types_to_discover:
            if ptype not in ENTRY_POINT_GROUPS:
                logger.warning("unknown_plugin_type", plugin_type=ptype)
                continue

            entry_point_group = ENTRY_POINT_GROUPS[ptype]

            logger.info(
                "plugin_discovery_started",
                plugin_type=ptype,
                entry_point_group=entry_point_group,
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
                    # Check if plugin is allowed
                    if not _is_plugin_allowed(entry_point.name):
                        continue

                    logger.info(
                        "plugin_loading",
                        plugin_name=entry_point.name,
                        entry_point=entry_point.value,
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
                            "plugin_invalid_base_class",
                            plugin_name=entry_point.name,
                        )
                        continue

                    # Validate specific plugin type
                    expected_type = _PLUGIN_EXPECTED_TYPES[ptype]

                    if not isinstance(plugin, expected_type):
                        logger.error(
                            "plugin_incorrect_type",
                            plugin_name=entry_point.name,
                            expected_type=expected_type.__name__,
                            actual_type=type(plugin).__name__,
                        )
                        continue

                    if auto_register:
                        _register_plugin_with_lifecycle(ptype, plugin, replace=True)

                    # Add to discovered plugins
                    discovered[ptype].append(plugin)

                    logger.info(
                        "plugin_loaded",
                        plugin_name=plugin.metadata.name,
                        plugin_version=plugin.metadata.version,
                        plugin_type=ptype,
                    )

                except Exception:
                    logger.error(
                        "plugin_load_failed",
                        plugin_name=entry_point.name,
                        entry_point=entry_point.value,
                        plugin_type=ptype,
                        exc_info=True,
                    )
                    continue

        # Log summary
        total = sum(len(plugins) for plugins in discovered.values())
        logger.info("plugin_discovery_completed", total_plugins=total, discovered=discovered)

        return discovered


def list_plugins(plugin_type: str | None = None) -> dict[str, list[str]]:
    """
    List all plugins in the global registry.

    Args:
        plugin_type: Optional plugin type to list ("source_connectors",
            "quality_checks", "transformations", "services", "catalogs"). If None, list all types.

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
        "services", "cli_commands", "hooks", "asset_providers", "resource_providers",
        "orchestrators", "catalogs")
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
    getter_method = _PLUGIN_GETTER_METHODS.get(plugin_type)
    if not getter_method:
        logger.warning("unknown_plugin_type", plugin_type=plugin_type)
        return None
    registry = get_global_registry()
    return getattr(registry, getter_method)(name)


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
            "services", "cli_commands", "hooks", "catalogs")
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
        getter_method = _PLUGIN_GETTER_METHODS.get(plugin_type)
        if not getter_method:
            continue
        getter = getattr(registry, getter_method)
        for name in plugin_names:
            plugin = getter(name)
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
    except Exception:
        logger.warning("plugin_auto_discover_failed", exc_info=True)


def _is_auto_discover_disabled_by_env() -> bool:
    """Return True when PHLO_NO_AUTO_DISCOVER explicitly disables discovery."""
    raw_value = os.environ.get(_NO_AUTO_DISCOVER_ENV)
    if raw_value is None:
        return False

    value = raw_value.strip().lower()
    if value in _FALSY_ENV_VALUES:
        return False
    if value not in _TRUTHY_ENV_VALUES:
        logger.warning(
            "plugin_auto_discover_env_invalid",
            env_var=_NO_AUTO_DISCOVER_ENV,
            value=raw_value,
            hint=f"Use {_NO_AUTO_DISCOVER_ENV}=1 to disable auto-discovery",
        )
    return True


def _should_auto_discover() -> bool:
    """Resolve auto-discovery using settings default plus env override precedence."""
    settings = get_settings()
    return settings.plugins_auto_discover and not _is_auto_discover_disabled_by_env()


# Auto-discover plugins when module is imported
# `plugins_auto_discover` is the default; `PHLO_NO_AUTO_DISCOVER` has override precedence.
if _should_auto_discover():
    try:
        auto_discover()
    except Exception as exc:
        logger.warning(
            "plugin_auto_discovery_failed",
            error=str(exc),
            hint=(
                "Set PHLO_NO_AUTO_DISCOVER=1 to skip auto-discovery "
                "or set plugins_auto_discover=false"
            ),
        )
