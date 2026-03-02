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
from phlo.plugins.discovery.registry import (
    PluginRegistry,
    get_global_registry,
)
from phlo.plugins.discovery.services import (
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
