"""Capability discovery for asset and resource providers."""

from __future__ import annotations

from phlo.capabilities.registry import register_asset, register_check, register_resource
from phlo.discovery import discover_plugins, get_global_registry
from phlo.logging import get_logger

logger = get_logger(__name__)


def discover_capabilities() -> None:
    """Discover capability providers and register their specs."""
    discover_plugins(plugin_type="asset_providers", auto_register=True)
    discover_plugins(plugin_type="resource_providers", auto_register=True)

    registry = get_global_registry()

    for name in registry.list_asset_providers():
        plugin = registry.get_asset_provider(name)
        if plugin is None:
            continue
        try:
            for asset in plugin.get_assets():
                register_asset(asset)
            for check in plugin.get_checks():
                register_check(check)
        except Exception as exc:
            logger.warning("Failed to load asset provider %s: %s", name, exc)

    for name in registry.list_resource_providers():
        plugin = registry.get_resource_provider(name)
        if plugin is None:
            continue
        try:
            for resource in plugin.get_resources():
                register_resource(resource)
        except Exception as exc:
            logger.warning("Failed to load resource provider %s: %s", name, exc)
