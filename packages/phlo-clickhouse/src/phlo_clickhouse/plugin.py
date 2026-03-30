"""ClickHouse service and resource provider plugins.

This module provides Phlo plugin implementations for ClickHouse integration,
including service management, resource provisioning, and capability discovery.

Example:
    Using the ClickHouse plugins:

    >>> from phlo_clickhouse.plugin import ClickHouseServicePlugin
    >>> plugin = ClickHouseServicePlugin()
    >>> plugin.metadata.name
    'clickhouse'

"""

from __future__ import annotations

from importlib import resources
from time import perf_counter
from typing import Any

import yaml

from phlo.capabilities import (
    CapabilitySupport,
    PublishTargetSpec,
    ResourceSpec,
    TableStoreSpec,
)
from phlo.capabilities.specs import QueryEngineSpec
from phlo.logging import get_logger
from phlo.plugins import PluginMetadata, ResourceProviderPlugin, ServicePlugin
from phlo_clickhouse.publish_target import ClickHousePublishTarget
from phlo_clickhouse.resource import CLICKHOUSE_QUERY_ENGINE_SUPPORT, ClickHouseResource
from phlo_clickhouse.settings import get_settings as get_clickhouse_settings

logger = get_logger(__name__)


def _load_service_definition(resource_name: str, service_name: str) -> dict[str, Any]:
    """Load and parse a YAML service definition from package resources.

    Reads a YAML service configuration file bundled with the package and
    parses it into a Python dictionary. Logs performance metrics and errors.

    Args:
        resource_name: Name of the YAML resource file to load.
        service_name: Identifier for the service being loaded (used in logs).

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        Exception: If the YAML file cannot be read or parsed. The error is
            logged with context before being re-raised.

    Example:
        >>> definition = _load_service_definition("service.yaml", "clickhouse")
        >>> "services" in definition
        True

    """
    start = perf_counter()
    logger.info(
        "clickhouse_service_definition_load_started",
        service_name=service_name,
        resource_name=resource_name,
    )
    service_path = resources.files("phlo_clickhouse").joinpath(resource_name)
    try:
        data = yaml.safe_load(service_path.read_text(encoding="utf-8"))
    except Exception:
        logger.error(
            "clickhouse_service_definition_load_failed",
            service_name=service_name,
            resource_name=resource_name,
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
            exc_info=True,
        )
        raise

    service_count = len(data.get("services", {})) if isinstance(data, dict) else None
    logger.info(
        "clickhouse_service_definition_load_completed",
        service_name=service_name,
        resource_name=resource_name,
        elapsed_ms=round((perf_counter() - start) * 1000, 2),
        service_count=service_count,
    )
    return data


class ClickHouseServicePlugin(ServicePlugin):
    """Service plugin for ClickHouse database service.

    Manages the ClickHouse database service lifecycle within Phlo's
    service orchestration framework.

    Example:
        >>> plugin = ClickHouseServicePlugin()
        >>> plugin.metadata.name
        'clickhouse'

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for service registration.

        Returns:
            PluginMetadata containing name, version, description,
            author, and tags for the ClickHouse service.

        """
        return PluginMetadata(
            name="clickhouse",
            version="0.1.0",
            description="ClickHouse analytical database for data plane",
            author="Phlo Team",
            tags=["data", "query", "storage"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Return Docker Compose service definition for ClickHouse.

        Returns:
            Dictionary containing Docker Compose service configuration
            loaded from the bundled service.yaml resource file.

        """
        return _load_service_definition("service.yaml", "clickhouse")


class ClickHouseSetupServicePlugin(ServicePlugin):
    """Service plugin for ClickHouse database initialization.

    Handles the initial setup and database creation for ClickHouse
    during the Phlo services initialization phase.

    Example:
        >>> plugin = ClickHouseSetupServicePlugin()
        >>> plugin.metadata.name
        'clickhouse-setup'

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for setup service registration.

        Returns:
            PluginMetadata for the ClickHouse setup service.

        """
        return PluginMetadata(
            name="clickhouse-setup",
            version="0.1.0",
            description="Initialize ClickHouse databases for data plane",
            author="Phlo Team",
            tags=["data", "bootstrap"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Return Docker Compose service definition for ClickHouse setup.

        Returns:
            Dictionary containing initialization service configuration
            loaded from the bundled clickhouse-setup.yaml resource file.

        """
        return _load_service_definition("clickhouse-setup.yaml", "clickhouse-setup")


class ClickHouseResourceProvider(ResourceProviderPlugin):
    """Resource provider plugin for ClickHouse.

    Provides ClickHouse resources, table stores, query engines, and
    publish targets to the Phlo capability framework.

    Example:
        >>> provider = ClickHouseResourceProvider()
        >>> resources = provider.get_resources()
        >>> len(resources)
        1

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for resource provider registration.

        Returns:
            PluginMetadata for the ClickHouse resource provider.

        """
        return PluginMetadata(
            name="clickhouse",
            version="0.1.0",
            description="ClickHouse resource for Phlo",
            support=CapabilitySupport(),
        )

    def get_resources(self) -> list[ResourceSpec]:
        """Return list of ClickHouse resource specifications.

        Returns:
            List containing a ResourceSpec for the ClickHouse resource.

        """
        return [ResourceSpec(name="clickhouse", resource=ClickHouseResource())]

    def get_table_stores(self) -> list[TableStoreSpec]:
        """Return list of ClickHouse table store specifications.

        Returns:
            List containing a TableStoreSpec for ClickHouse with
            capability flags for schema evolution support.

        """
        return [
            TableStoreSpec(
                name="clickhouse",
                provider=ClickHouseResource(),
                support=CapabilitySupport(
                    supports_snapshots=False,
                    supports_schema_evolution=True,
                ),
            )
        ]

    def get_query_engines(self) -> list[QueryEngineSpec]:
        """Return list of ClickHouse query engine specifications.

        Reads current settings to populate connection metadata including
        host, port, and database information.

        Returns:
            List containing a QueryEngineSpec for ClickHouse with
            full connection metadata and capability support flags.

        """
        settings = get_clickhouse_settings()
        return [
            QueryEngineSpec(
                name="clickhouse",
                provider=ClickHouseResource(),
                metadata={
                    "host": settings.clickhouse_host,
                    "port": settings.clickhouse_http_port,
                    "native_port": settings.clickhouse_native_port,
                    "default_database": settings.clickhouse_db,
                    "service_type": "ClickHouse",
                },
                support=CLICKHOUSE_QUERY_ENGINE_SUPPORT,
            )
        ]

    def get_publish_targets(self) -> list[PublishTargetSpec]:
        """Return list of ClickHouse publish target specifications.

        Returns:
            List containing a PublishTargetSpec for the ClickHouse
            data mart publishing target.

        """
        return [
            PublishTargetSpec(
                name="clickhouse",
                provider=ClickHousePublishTarget(),
                metadata={"target_system": "clickhouse", "role": "serving"},
            )
        ]
