"""
Unified Discovery Module

Consolidates plugin and service discovery into a single module.

This module provides a unified interface for discovering:
- Plugins (via entry points)
- Services (from plugins and core)
- Plugin registry (remote package search)
"""

from phlo.discovery.plugins import (
    ENTRY_POINT_GROUPS,
    discover_plugins,
    get_plugin,
    get_plugin_info,
    get_quality_check,
    get_service,
    get_source_connector,
    get_transformation,
    list_plugins,
    validate_plugins,
)
from phlo.discovery.registry import (
    PluginRegistry,
    get_global_registry,
)
from phlo.discovery.services import (
    ServiceDefinition,
    ServiceDiscovery,
)

__all__ = [
    # Plugin discovery
    "ENTRY_POINT_GROUPS",
    "discover_plugins",
    "get_plugin",
    "get_plugin_info",
    "get_quality_check",
    "get_service",
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
