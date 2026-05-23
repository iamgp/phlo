"""Capability discovery for asset and resource providers."""

from __future__ import annotations

from phlo.capabilities.observability import register_default_capability_providers
from phlo.capabilities.registry import (
    iter_provider_capabilities,
    register_capability,
)
from phlo.logging import get_logger
from phlo.plugins.discovery import discover_plugins, get_global_registry

logger = get_logger(__name__)


def discover_capabilities() -> None:
    """Discover capability providers and register their specs."""
    logger.info("capability_discovery_started")
    register_default_capability_providers()
    discover_plugins(plugin_type="asset_providers", auto_register=True)
    discover_plugins(plugin_type="resource_providers", auto_register=True)

    registry = get_global_registry()

    asset_provider_count = 0
    for name in registry.list_asset_providers():
        plugin = registry.get_asset_provider(name)
        if plugin is None:
            continue
        asset_provider_count += 1
        try:
            for family, specs in iter_provider_capabilities(plugin):
                for spec in specs:
                    register_capability(family, spec)
        except Exception as exc:
            logger.warning(
                "capability_asset_provider_registration_failed",
                provider_name=name,
                error=str(exc),
                exc_info=True,
            )

    resource_provider_count = 0
    for name in registry.list_resource_providers():
        plugin = registry.get_resource_provider(name)
        if plugin is None:
            continue
        resource_provider_count += 1
        try:
            for family, specs in iter_provider_capabilities(plugin):
                for spec in specs:
                    register_capability(family, spec)
        except Exception as exc:
            missing_optional_config = "must be provided" in str(exc)
            logger.warning(
                "capability_resource_provider_registration_failed",
                provider_name=name,
                error=str(exc),
                exc_info=not missing_optional_config,
            )

    logger.info(
        "capability_discovery_completed",
        asset_provider_count=asset_provider_count,
        resource_provider_count=resource_provider_count,
    )
