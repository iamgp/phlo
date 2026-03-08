"""ClickHouse service and resource provider plugins."""

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
    """Service plugin for ClickHouse."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="clickhouse",
            version="0.1.0",
            description="ClickHouse analytical database for data plane",
            author="Phlo Team",
            tags=["data", "query", "storage"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        return _load_service_definition("service.yaml", "clickhouse")


class ClickHouseSetupServicePlugin(ServicePlugin):
    """Service plugin for ClickHouse database initialization."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="clickhouse-setup",
            version="0.1.0",
            description="Initialize ClickHouse databases for data plane",
            author="Phlo Team",
            tags=["data", "bootstrap"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        return _load_service_definition("clickhouse-setup.yaml", "clickhouse-setup")


class ClickHouseResourceProvider(ResourceProviderPlugin):
    """Resource provider plugin for ClickHouse."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="clickhouse",
            version="0.1.0",
            description="ClickHouse resource for Phlo",
            support=CapabilitySupport(),
        )

    def get_resources(self) -> list[ResourceSpec]:
        return [ResourceSpec(name="clickhouse", resource=ClickHouseResource())]

    def get_table_stores(self) -> list[TableStoreSpec]:
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
        settings = get_clickhouse_settings()
        return [
            QueryEngineSpec(
                name="clickhouse",
                provider=ClickHouseResource(),
                metadata={
                    "host": settings.clickhouse_host,
                    "port": settings.clickhouse_http_port,
                    "native_port": settings.clickhouse_native_port,
                    "default_database": settings.clickhouse_database,
                    "service_type": "ClickHouse",
                },
                support=CLICKHOUSE_QUERY_ENGINE_SUPPORT,
            )
        ]

    def get_publish_targets(self) -> list[PublishTargetSpec]:
        return [
            PublishTargetSpec(
                name="clickhouse",
                provider=ClickHousePublishTarget(),
                metadata={"target_system": "clickhouse", "role": "serving"},
            )
        ]
