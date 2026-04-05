"""Lifecycle-aware registration helpers for discovered plugins."""

from __future__ import annotations

from phlo.logging import get_logger
from phlo.plugins.base import Plugin
from phlo.plugins.discovery._plugin_constants import (
    PLUGIN_GETTER_METHODS,
    PLUGIN_REGISTER_METHODS,
)
from phlo.plugins.discovery.registry import get_global_registry

logger = get_logger(__name__)


def register_plugin_with_lifecycle(plugin_type: str, plugin: Plugin, replace: bool = True) -> None:
    """Register plugin with initialize/cleanup lifecycle hooks and rollback safeguards."""
    registry = get_global_registry()
    register_method_name = PLUGIN_REGISTER_METHODS.get(plugin_type)
    getter_method_name = PLUGIN_GETTER_METHODS.get(plugin_type)

    if not register_method_name or not getter_method_name:
        raise ValueError(f"Unknown plugin type: {plugin_type}")

    register_method = getattr(registry, register_method_name)
    existing_plugin = getattr(registry, getter_method_name)(plugin.metadata.name)

    if existing_plugin and not replace:
        raise ValueError(
            f"Plugin '{plugin.metadata.name}' of type '{plugin_type}' is already registered. "
            "Use replace=True to overwrite."
        )

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
