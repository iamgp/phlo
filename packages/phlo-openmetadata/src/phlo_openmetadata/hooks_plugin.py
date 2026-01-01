"""Hook plugin for OpenMetadata integration."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from phlo.config import get_settings
from phlo.hooks import LineageEvent, PublishEvent, QualityResultEvent
from phlo.plugins.base import PluginMetadata
from phlo.plugins.hooks import HookFilter, HookPlugin, HookRegistration

from phlo_openmetadata.openmetadata import OpenMetadataClient, OpenMetadataTable
from phlo_openmetadata.quality_sync import QualityCheckMapper

logger = logging.getLogger(__name__)


class OpenMetadataHookPlugin(HookPlugin):
    def __init__(self) -> None:
        """Initialize the plugin with lazy client setup."""

        self._client: OpenMetadataClient | None = None

    @property
    def metadata(self) -> PluginMetadata:
        """Metadata for the OpenMetadata hook plugin."""

        return PluginMetadata(
            name="openmetadata",
            version="0.1.0",
            description="Hook handlers for OpenMetadata metadata and quality sync",
        )

    def get_hooks(self) -> list[HookRegistration]:
        """Register lineage, quality, and publish hook handlers."""

        return [
            HookRegistration(
                hook_name="openmetadata_lineage",
                handler=self._handle_lineage,
                filters=HookFilter(event_types={"lineage.edges"}),
            ),
            HookRegistration(
                hook_name="openmetadata_quality",
                handler=self._handle_quality_result,
                filters=HookFilter(event_types={"quality.result"}),
            ),
            HookRegistration(
                hook_name="openmetadata_publish",
                handler=self._handle_publish,
                filters=HookFilter(event_types={"publish.end"}),
            ),
        ]

    def cleanup(self) -> None:
        """Close the OpenMetadata client if initialized."""

        if self._client:
            self._client.close()
            self._client = None

    def _handle_lineage(self, event: Any) -> None:
        """Sync lineage edges into OpenMetadata."""

        if not isinstance(event, LineageEvent):
            return
        client = self._get_client()
        if client is None:
            return
        for from_fqn, to_fqn in event.edges:
            try:
                client.create_lineage(from_fqn, to_fqn)
            except Exception as exc:
                logger.warning("OpenMetadata lineage sync failed: %s", exc)

    def _handle_quality_result(self, event: Any) -> None:
        """Sync quality results into OpenMetadata test metadata."""

        if not isinstance(event, QualityResultEvent):
            return
        client = self._get_client()
        if client is None:
            return

        table_fqn = _resolve_table_fqn(event)
        if not table_fqn:
            logger.warning("OpenMetadata quality sync skipped: missing table_fqn")
            return

        test_name = event.check_name
        test_type = _resolve_test_type(event)
        try:
            client.create_test_definition(test_name=test_name, test_type=test_type)
        except Exception as exc:
            logger.warning("OpenMetadata test definition sync failed: %s", exc)

        test_case_name = f"{table_fqn}_{test_name}"
        test_case_fqn = test_case_name
        try:
            test_case = client.create_test_case(
                test_case_name=test_case_name,
                table_fqn=table_fqn,
                test_definition_name=test_name,
            )
            test_case_fqn = (
                test_case.get("fullyQualifiedName") or test_case.get("name") or test_case_name
            )
        except Exception as exc:
            logger.warning("OpenMetadata test case sync failed: %s", exc)

        result_value = event.metadata.get("metric_value")
        try:
            client.publish_test_result(
                test_case_fqn=test_case_fqn,
                result="Success" if event.passed else "Failed",
                test_execution_date=datetime.now(timezone.utc),
                result_value=str(result_value) if result_value is not None else None,
            )
        except Exception as exc:
            logger.warning("OpenMetadata test result publish failed: %s", exc)

    def _handle_publish(self, event: Any) -> None:
        """Sync published tables into OpenMetadata."""

        if not isinstance(event, PublishEvent):
            return
        if event.status != "success":
            return
        client = self._get_client()
        if client is None:
            return

        settings = get_settings()
        for target_table, target_fqn in event.tables.items():
            schema_name, table_name = _split_table_fqn(
                target_fqn,
                default_schema=settings.postgres_mart_schema,
            )
            try:
                table = OpenMetadataTable(name=table_name)
                client.create_or_update_table(schema_name=schema_name, table=table)
            except Exception as exc:
                logger.warning(
                    "OpenMetadata publish sync failed for %s: %s",
                    target_table,
                    exc,
                )

    def _get_client(self) -> OpenMetadataClient | None:
        """Return the OpenMetadata client if sync is enabled."""

        settings = get_settings()
        if not settings.openmetadata_sync_enabled:
            return None
        if self._client is None:
            self._client = OpenMetadataClient(
                base_url=settings.openmetadata_uri,
                username=settings.openmetadata_username,
                password=settings.openmetadata_password,
                verify_ssl=settings.openmetadata_verify_ssl,
                service_name=settings.openmetadata_service_name,
                service_type=settings.openmetadata_service_type,
                database_name=settings.openmetadata_database,
            )
        return self._client


def _resolve_table_fqn(event: QualityResultEvent) -> str | None:
    """Resolve the table FQN from quality event metadata."""

    for key in ("table_fqn", "table_name", "table"):
        value = event.metadata.get(key)
        if isinstance(value, str) and value:
            return value
    if event.asset_key:
        return event.asset_key
    return None


def _resolve_test_type(event: QualityResultEvent) -> str:
    """Map quality check types to OpenMetadata test types."""

    check_type = event.check_type or ""
    if check_type.lower() == "pandera":
        return "schemaCheck"
    return QualityCheckMapper.CHECK_TYPE_MAP.get(check_type, "customCheck")


def _split_table_fqn(table_fqn: str, default_schema: str) -> tuple[str, str]:
    """Split a table FQN into schema and table name components."""

    if "." not in table_fqn:
        return default_schema, table_fqn
    schema_name, table_name = table_fqn.split(".", 1)
    return schema_name, table_name
