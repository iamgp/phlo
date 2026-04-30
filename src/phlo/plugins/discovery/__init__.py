"""
Plugin Discovery Module

Consolidates plugin and service discovery into a single module under phlo.plugins.

This module provides a unified interface for discovering:
- Plugins (via entry points)
- Services (from plugins and core)
- Local in-memory registry access

Remote registry package discovery lives in phlo.plugins.registry_client
(e.g., list_registry_plugins) and is not re-exported here.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from phlo.plugins.discovery.registry import (
    PluginRegistry,
    get_global_registry,
)
from phlo.plugins.discovery.services import (
    ServiceDefinition,
    ServiceDiscovery,
)

if TYPE_CHECKING:
    from phlo.plugins.discovery.plugins import (
        ENTRY_POINT_GROUPS,
        discover_plugins,
        get_hook_plugin,
        get_ingestion_provider,
        get_plugin,
        get_plugin_info,
        get_quality_check,
        get_quality_provider,
        get_service,
        get_source_connector,
        get_transformation,
        get_transformation_provider,
        list_plugins,
        validate_plugins,
    )

_PLUGIN_EXPORTS = frozenset(
    {
        "ENTRY_POINT_GROUPS",
        "discover_plugins",
        "get_plugin",
        "get_plugin_info",
        "get_quality_check",
        "get_quality_provider",
        "get_ingestion_provider",
        "get_transformation_provider",
        "get_service",
        "get_hook_plugin",
        "get_source_connector",
        "get_transformation",
        "list_plugins",
        "validate_plugins",
    }
)


def __getattr__(name: str):
    """Lazily expose entry-point plugin discovery helpers.

    Importing service discovery or hook emitters must not eagerly import every
    installed plugin. Doing so can re-enter discovery while provider modules are
    still being initialized.
    """
    if name in _PLUGIN_EXPORTS:
        plugins_module = importlib.import_module("phlo.plugins.discovery.plugins")
        return getattr(plugins_module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Plugin discovery
    "ENTRY_POINT_GROUPS",
    "discover_plugins",
    "get_plugin",
    "get_plugin_info",
    "get_quality_check",
    "get_quality_provider",
    "get_ingestion_provider",
    "get_transformation_provider",
    "get_service",
    "get_hook_plugin",
    "get_source_connector",
    "get_transformation",
    "list_plugins",
    "validate_plugins",
    # Registry
    "PluginRegistry",
    "get_global_registry",
    # Service discovery
    "ServiceDefinition",
    "ServiceDiscovery",
]
