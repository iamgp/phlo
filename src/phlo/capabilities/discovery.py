"""Capability discovery for asset and resource providers."""

from __future__ import annotations

from phlo.capabilities.registry import (
    register_asset,
    register_catalog,
    register_check,
    register_lineage_sink,
    register_metadata_catalog,
    register_quality_backend,
    register_query_engine,
    register_resource,
    register_table_store,
)
from phlo.logging import get_logger
from phlo.plugins.discovery import discover_plugins, get_global_registry

logger = get_logger(__name__)


def discover_capabilities() -> None:
    """Discover capability providers and register their specs."""
    logger.info("capability_discovery_started")
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
            for asset in plugin.get_assets():
                register_asset(asset)
            for check in plugin.get_checks():
                register_check(check)
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
            for resource in plugin.get_resources():
                register_resource(resource)
            for table_store in plugin.get_table_stores():
                register_table_store(table_store)
            for catalog in plugin.get_catalogs():
                register_catalog(catalog)
            for query_engine in plugin.get_query_engines():
                register_query_engine(query_engine)
            for quality_backend in plugin.get_quality_backends():
                register_quality_backend(quality_backend)
            for metadata_catalog in plugin.get_metadata_catalogs():
                register_metadata_catalog(metadata_catalog)
            for lineage_sink in plugin.get_lineage_sinks():
                register_lineage_sink(lineage_sink)
        except Exception as exc:
            logger.warning(
                "capability_resource_provider_registration_failed",
                provider_name=name,
                error=str(exc),
                exc_info=True,
            )

    logger.info(
        "capability_discovery_completed",
        asset_provider_count=asset_provider_count,
        resource_provider_count=resource_provider_count,
    )
