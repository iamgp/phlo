"""Query helpers for discovered and registered plugins."""

from __future__ import annotations

from phlo.logging import get_logger
from phlo.plugins.base import (
    Plugin,
    QualityCheckPlugin,
    ServicePlugin,
    SourceConnectorPlugin,
    TransformationPlugin,
)
from phlo.plugins.discovery._plugin_constants import PLUGIN_GETTER_METHODS
from phlo.plugins.discovery.registry import get_global_registry
from phlo.plugins.hooks import HookPlugin

logger = get_logger(__name__)


def list_plugins(plugin_type: str | None = None) -> dict[str, list[str]]:
    """List all plugins in the global registry."""
    registry = get_global_registry()
    all_plugins = registry.list_all_plugins()

    if plugin_type:
        if plugin_type not in all_plugins:
            return {plugin_type: []}
        return {plugin_type: all_plugins[plugin_type]}

    return all_plugins


def get_plugin(plugin_type: str, name: str) -> Plugin | None:
    """Get a plugin by type and name."""
    getter_method = PLUGIN_GETTER_METHODS.get(plugin_type)
    if not getter_method:
        logger.warning("unknown_plugin_type", plugin_type=plugin_type)
        return None

    registry = get_global_registry()
    return getattr(registry, getter_method)(name)


def get_source_connector(name: str) -> SourceConnectorPlugin | None:
    """Get a source connector plugin by name."""
    registry = get_global_registry()
    return registry.get_source_connector(name)


def get_quality_check(name: str) -> QualityCheckPlugin | None:
    """Get a quality check plugin by name."""
    registry = get_global_registry()
    return registry.get_quality_check(name)


def get_transformation(name: str) -> TransformationPlugin | None:
    """Get a transformation plugin by name."""
    registry = get_global_registry()
    return registry.get_transformation(name)


def get_service(name: str) -> ServicePlugin | None:
    """Get a service plugin by name."""
    registry = get_global_registry()
    return registry.get_service(name)


def get_hook_plugin(name: str) -> HookPlugin | None:
    """Get a hook plugin by name."""
    registry = get_global_registry()
    return registry.get_hook_plugin(name)


def get_plugin_info(plugin_type: str, name: str) -> dict | None:
    """Get detailed metadata for a plugin."""
    registry = get_global_registry()
    return registry.get_plugin_metadata(plugin_type, name)


def validate_plugins() -> dict[str, list[str]]:
    """Validate all registered plugins."""
    registry = get_global_registry()
    all_plugins = registry.list_all_plugins()

    valid: list[str] = []
    invalid: list[str] = []

    for current_type, plugin_names in all_plugins.items():
        getter_method = PLUGIN_GETTER_METHODS.get(current_type)
        if not getter_method:
            continue

        getter = getattr(registry, getter_method)
        for plugin_name in plugin_names:
            plugin = getter(plugin_name)
            if plugin and registry.validate_plugin(plugin):
                valid.append(f"{current_type}:{plugin_name}")
            else:
                invalid.append(f"{current_type}:{plugin_name}")

    return {"valid": valid, "invalid": invalid}
