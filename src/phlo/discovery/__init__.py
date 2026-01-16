"""
Unified Discovery Module (Backwards Compatibility Shim)

This module re-exports from phlo.plugins.discovery for backwards compatibility.
New code should import directly from phlo.plugins.discovery.

Consolidates plugin and service discovery into a single module.

This module provides a unified interface for discovering:
- Plugins (via entry points)
- Services (from plugins and core)
- Plugin registry (remote package search)
"""

from phlo.plugins.discovery import (
    ENTRY_POINT_GROUPS,
    PluginRegistry,
    ServiceDefinition,
    ServiceDiscovery,
    discover_plugins,
    get_global_registry,
    get_hook_plugin,
    get_plugin,
    get_plugin_info,
    get_quality_check,
    get_service,
    get_source_connector,
    get_transformation,
    list_plugins,
    validate_plugins,
)

__all__ = [
    # Plugin discovery
    "ENTRY_POINT_GROUPS",
    "discover_plugins",
    "get_plugin",
    "get_plugin_info",
    "get_quality_check",
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
