"""IcebergResource dataclass for asset/resource access.

This module provides the ``IcebergResource`` dataclass, which serves as a
high-level interface for Iceberg operations within Dagster assets and resources.
It wraps table operations, snapshot management, and schema conversion in a
convenient API suitable for use as a Dagster resource.

The resource is designed to work with Phlo's capability system and supports
branching via Nessie references.

Example:
    Using IcebergResource in a Dagster asset::

        from dagster import asset
        from phlo_iceberg import IcebergResource

        @asset
        def processed_events(iceberg: IcebergResource):
            # Ensure table exists
            from pyiceberg.schema import Schema
            from pyiceberg.types import NestedField, LongType, StringType

            schema = Schema(
                NestedField(1, "id", LongType(), required=True),
                NestedField(2, "data", StringType(), required=False),
            )
            iceberg.ensure_table("raw.events", schema=schema)

            # Append data
            result = iceberg.append_parquet(
                table_name="raw.events",
                data_path="/data/events.parquet"
            )
            return result

    Resource configuration::

        from dagster import Definitions
        from phlo_iceberg import IcebergResource

        defs = Definitions(
            resources={
                "iceberg": IcebergResource(ref="main")
            }
        )

"""

from collections.abc import Sequence
from dataclasses import dataclass, field
import re
from typing import Any

from pandera.pandas import DataFrameModel
from pyiceberg.catalog import Catalog
from pyiceberg.schema import Schema
from pyiceberg.table import Table

from phlo.capabilities import (
    MaintenanceExecutionError,
    MaintenanceExecutionPhase,
    MaintenanceOperationResult,
    MaintenanceOperationState,
    MaintenancePreconditionError,
)
from phlo.capabilities.interfaces import MaintenanceExecutor
from phlo.capabilities.interfaces import TableStoreSupport
from phlo.logging import get_logger
from phlo_iceberg.catalog import get_catalog
from phlo_iceberg.settings import get_settings
from phlo_iceberg.tables import (
    append_to_table,
    delete_rows_from_table,
    ensure_table,
    expire_snapshots,
    get_table_stats,
    list_table_snapshots,
    merge_to_table,
    overwrite_table,
    remove_orphan_files,
    rollback_table_to_snapshot,
)

logger = get_logger(__name__)

_COMPACTION_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_compaction_table_name(table_name: str) -> str:
    """Validate and quote the namespace.table relation used by Trino."""
    parts = table_name.split(".")
    if len(parts) != 2 or any(not _COMPACTION_IDENTIFIER.fullmatch(part) for part in parts):
        raise ValueError(
            "Compaction table_name must be a namespace.table identifier containing only "
            "letters, numbers, and underscores."
        )
    return ".".join(f'"{part}"' for part in parts)


def _compaction_failure(
    exc: Exception,
    *,
    code: str,
    retryable: bool | None = None,
) -> dict[str, object]:
    """Normalize provider failures without losing retry guidance."""
    message = str(exc).strip() or type(exc).__name__
    lowered = message.lower()
    if retryable is None:
        retryable = any(
            marker in lowered
            for marker in ("timeout", "temporarily unavailable", "connection", "concurrent")
        )
    return {
        "code": code,
        "type": type(exc).__name__,
        "message": message,
        "retryable": retryable,
    }


def _blocked_compaction_result(
    *,
    table_name: str,
    ref: str,
    operation_id: str | None,
    before_snapshot_id: int | None,
    plan: dict[str, object],
    code: str,
    message: str,
    details: dict[str, object],
) -> dict[str, object]:
    return MaintenanceOperationResult(
        operation="compact",
        table_name=table_name,
        ref=ref,
        dry_run=False,
        status=MaintenanceOperationState.BLOCKED,
        accepted=False,
        executed=False,
        before_snapshot_id=before_snapshot_id,
        planned=plan,
        evidence={
            "before": {
                "snapshot_id": before_snapshot_id,
                "file_count": plan.get("file_count", 0),
                "snapshot_count": plan.get("snapshot_count", 0),
            }
        },
        failure={"code": code, "type": "PreconditionError", "message": message, **details},
        operation_id=operation_id,
        retry_safe=True,
    ).to_dict()


@dataclass
class IcebergResource:
    """Resource wrapper for Iceberg REST catalog operations.

    Provides a high-level interface for common Iceberg table operations
    including data ingestion (append, merge, overwrite), snapshot management,
    and schema conversion. Designed for use as a Dagster resource.

    Attributes:
        ref: Nessie branch/tag reference for all operations. Defaults to
            the value from settings (typically ``main``).

    Example:
        Basic resource usage::

            iceberg = IcebergResource(ref="main")

            # Work with catalog
            catalog = iceberg.get_catalog()

            # Convert Pandera schema
            schema = iceberg.schema_from_validation_schema(MyPanderaModel)

            # Ensure table exists
            table = iceberg.ensure_table("raw.events", schema=schema)

            # Append data
            result = iceberg.append_parquet("raw.events", "/data/events.parquet")
            print(f"Inserted {result['rows_inserted']} rows")

    """

    ref: str = field(default_factory=lambda: get_settings().iceberg_default_ref)

    @property
    def support(self) -> TableStoreSupport:
        """Return Iceberg table-store support metadata."""
        return TableStoreSupport(
            supports_refs=True,
            partition_transforms=frozenset({"identity", "day", "hour", "month", "year"}),
            supports_snapshots=True,
            supports_compaction=True,
            supports_vacuum=True,
        )

    def get_catalog(self, override_ref: str | None = None) -> Catalog:
        """Return an Iceberg catalog client for the active branch.

        Args:
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            Catalog: Configured PyIceberg catalog instance.

        Example:
            Access catalog directly::

                iceberg = IcebergResource(ref="main")
                catalog = iceberg.get_catalog()

                # Access low-level catalog methods
                table = catalog.load_table("raw.events")

                # Or use different branch
                dev_catalog = iceberg.get_catalog(override_ref="dev-branch")

        """
        branch = override_ref or self.ref
        return get_catalog(ref=branch)

    def schema_from_validation_schema(
        self, validation_schema: type[DataFrameModel] | type[Any]
    ) -> Schema:
        """Convert a Pandera validation model to an Iceberg schema.

        Useful for ingestion flows where data is validated using Pandera
        models before being written to Iceberg.

        Args:
            validation_schema: Pandera DataFrameModel class to convert.

        Returns:
            Schema: Iceberg schema equivalent to the Pandera model.

        Raises:
            SchemaConversionError: If the Pandera schema cannot be converted.

        Example:
            Convert Pandera model to Iceberg schema::

                from pandera import DataFrameModel, Column, Int64, String

                class UserSchema(DataFrameModel):
                    id: Column[Int64]
                    name: Column[String]

                iceberg = IcebergResource()
                schema = iceberg.schema_from_validation_schema(UserSchema)
                table = iceberg.ensure_table("raw.users", schema=schema)

        """
        from phlo_iceberg.schema_conversion import pandera_to_iceberg

        return pandera_to_iceberg(validation_schema)

    def ensure_table(
        self,
        table_name: str,
        schema: Schema,
        partition_spec: Sequence[tuple[str, str]] | None = None,
        override_ref: str | None = None,
    ) -> Table:
        """Ensure a table exists and return its handle.

        Creates the table if it doesn't exist, otherwise returns the existing table.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            schema: Iceberg table schema.
            partition_spec: Optional list of ``(field, transform)`` partition rules.
                Supported transforms: ``identity``, ``day``, ``hour``, ``month``, ``year``.
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            Table: Existing or newly created Iceberg table handle.

        Example:
            Ensure table with partitioning::

                from pyiceberg.schema import Schema
                from pyiceberg.types import NestedField, LongType, TimestamptzType

                schema = Schema(
                    NestedField(1, "id", LongType(), required=True),
                    NestedField(2, "ts", TimestamptzType(), required=True),
                )

                table = iceberg.ensure_table(
                    "raw.events",
                    schema=schema,
                    partition_spec=[("ts", "day")]
                )

        """
        branch = override_ref or self.ref
        return ensure_table(
            table_name=table_name,
            schema=schema,
            partition_spec=list(partition_spec) if partition_spec else None,
            ref=branch,
        )

    def append_parquet(
        self, table_name: str, data_path: str, override_ref: str | None = None
    ) -> dict[str, int]:
        """Append Parquet data into an Iceberg table.

        Reads data from a Parquet file or directory and appends it to the
        specified table. Automatically aligns schema and handles missing columns.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            data_path: Path to Parquet input data (file or directory).
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Write statistics from the append operation:
                - ``rows_inserted``: Number of rows appended.
                - ``rows_deleted``: Always 0.

        Raises:
            Exception: Re-raises any errors during append.

        Example:
            Simple append::

                result = iceberg.append_parquet(
                    table_name="raw.events",
                    data_path="/data/events_2024-01-01.parquet"
                )

            Append to specific branch::

                result = iceberg.append_parquet(
                    table_name="raw.events",
                    data_path="/data/events.parquet",
                    override_ref="dev-branch"
                )

        """
        branch = override_ref or self.ref
        logger.info(
            "iceberg_resource_append_requested",
            table_name=table_name,
            ref=branch,
            source=data_path,
        )
        try:
            result = append_to_table(table_name=table_name, data_path=data_path, ref=branch)
        except Exception as exc:
            logger.error(
                "iceberg_resource_append_failed",
                table_name=table_name,
                ref=branch,
                source=data_path,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "iceberg_resource_append_completed",
            table_name=table_name,
            ref=branch,
            source=data_path,
            rows_inserted=result.get("rows_inserted", 0),
            rows_deleted=result.get("rows_deleted", 0),
        )
        return result

    def merge_parquet(
        self,
        table_name: str,
        data_path: str,
        unique_key: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Merge (upsert) Parquet data into an Iceberg table using a unique key.

        Deletes existing rows with matching unique key values, then inserts
        the new data. This implements an upsert pattern useful for
        idempotent data loads.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            data_path: Path to Parquet input data (file or directory).
            unique_key: Column name used to identify and match existing rows.
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Write statistics from the merge operation:
                - ``rows_deleted``: Approximate count of rows deleted.
                - ``rows_inserted``: Number of rows inserted.

        Raises:
            Exception: Re-raises any errors during merge.

        Example:
            Upsert user data by ID::

                result = iceberg.merge_parquet(
                    table_name="raw.users",
                    data_path="/data/user_updates.parquet",
                    unique_key="user_id"
                )
                print(f"Updated ~{result['rows_deleted']} rows")
                print(f"Inserted {result['rows_inserted']} rows")

        Note:
            The ``rows_deleted`` count is an approximation because Iceberg
            doesn't report the actual number of rows deleted during the operation.

        """
        branch = override_ref or self.ref
        logger.info(
            "iceberg_resource_merge_requested",
            table_name=table_name,
            ref=branch,
            source=data_path,
            unique_key=unique_key,
        )
        try:
            result = merge_to_table(
                table_name=table_name,
                data_path=data_path,
                unique_key=unique_key,
                ref=branch,
            )
        except Exception as exc:
            logger.error(
                "iceberg_resource_merge_failed",
                table_name=table_name,
                ref=branch,
                source=data_path,
                unique_key=unique_key,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "iceberg_resource_merge_completed",
            table_name=table_name,
            ref=branch,
            source=data_path,
            unique_key=unique_key,
            rows_inserted=result.get("rows_inserted", 0),
            rows_deleted=result.get("rows_deleted", 0),
        )
        return result

    def overwrite_parquet(
        self, *, table_name: str, data_path: str, override_ref: str | None = None
    ) -> dict[str, int]:
        """Overwrite an Iceberg table with staged Parquet data.

        Replaces all existing data with the new data, creating a new snapshot.
        Previous data remains accessible via snapshot history until snapshots
        are expired.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            data_path: Path to Parquet input data (file or directory).
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Write statistics from the overwrite operation:
                - ``rows_inserted``: Number of rows in replacement data.
                - ``rows_deleted``: Always 0.

        Raises:
            Exception: Re-raises any errors during overwrite.

        Example:
            Regenerate summary table::

                result = iceberg.overwrite_parquet(
                    table_name="analytics.daily_summary",
                    data_path="/data/regenerated_summary.parquet"
                )
                print(f"Table now has {result['rows_inserted']} rows")

        """
        branch = override_ref or self.ref
        logger.info(
            "iceberg_resource_overwrite_requested",
            table_name=table_name,
            ref=branch,
            source=data_path,
        )
        try:
            result = overwrite_table(table_name=table_name, data_path=data_path, ref=branch)
        except Exception as exc:
            logger.error(
                "iceberg_resource_overwrite_failed",
                table_name=table_name,
                ref=branch,
                source=data_path,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "iceberg_resource_overwrite_completed",
            table_name=table_name,
            ref=branch,
            source=data_path,
            rows_inserted=result.get("rows_inserted", 0),
            rows_deleted=result.get("rows_deleted", 0),
        )
        return result

    def delete_rows(
        self, *, table_name: str, predicate: str, override_ref: str | None = None
    ) -> dict[str, int]:
        """Delete rows matching a predicate expression.

        Uses Iceberg's delete operation with a SQL-style predicate expression.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            predicate: Filter expression string (e.g., ``"status = 'inactive'"``).
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Delete statistics:
                - ``rows_deleted``: Always -1 (PyIceberg doesn't return count).

        Raises:
            Exception: Re-raises any errors during deletion.

        Example:
            Delete old records::

                iceberg.delete_rows(
                    table_name="raw.events",
                    predicate="event_time < '2024-01-01'"
                )

            Delete by status::

                iceberg.delete_rows(
                    table_name="raw.users",
                    predicate="account_status = 'deleted'"
                )

        Note:
            PyIceberg does not return the number of rows deleted, so
            ``rows_deleted`` is always -1.

        """
        branch = override_ref or self.ref
        logger.info(
            "iceberg_resource_delete_rows_requested",
            table_name=table_name,
            ref=branch,
            predicate=predicate,
        )
        try:
            result = delete_rows_from_table(table_name=table_name, predicate=predicate, ref=branch)
        except Exception as exc:
            logger.error(
                "iceberg_resource_delete_rows_failed",
                table_name=table_name,
                ref=branch,
                predicate=predicate,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "iceberg_resource_delete_rows_completed",
            table_name=table_name,
            ref=branch,
            predicate=predicate,
        )
        return result

    def compact(
        self,
        *,
        table_name: str,
        override_ref: str | None = None,
        dry_run: bool = False,
        expected_snapshot_id: int | str | None = None,
        operation_id: str | None = None,
        executor: MaintenanceExecutor | None = None,
    ) -> dict[str, object]:
        """Compact small files through the configured Trino Iceberg catalog.

        A dry run reads Iceberg metadata and returns the snapshot token required
        for an execute call. Execute mode takes an optimistic snapshot
        precondition. The executor owns the provider boundary and must target
        the requested ref. Execution is at-least-once: successful, no-op, and
        precondition outcomes are retry-safe, while a provider error after
        submission is reported as outcome-unknown and must be reconciled before
        retrying.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            override_ref: Optional branch or tag to use instead of ``self.ref``.
            dry_run: Inspect the table and plan the operation without invoking Trino.
            expected_snapshot_id: Snapshot observed by the caller. When omitted,
                execute mode captures and rechecks the current snapshot itself.
            operation_id: Optional caller-supplied correlation token. The current
                contract is at-least-once and does not provide durable deduplication.
            executor: Provider-neutral maintenance executor, such as the Trino
                capability provider. It is not invoked during a dry run.

        Returns:
            A provider-neutral operation result with plan, execution, and failure
            evidence.

        Raises:
            ValueError: If the table identifier is invalid.

        """
        branch = override_ref or self.ref
        quoted_table_name = _validate_compaction_table_name(table_name)

        try:
            before_snapshot_id, before_stats = self._compaction_metadata(table_name, branch)
        except Exception as exc:  # noqa: BLE001 - return structured operation evidence
            return MaintenanceOperationResult(
                operation="compact",
                table_name=table_name,
                ref=branch,
                dry_run=dry_run,
                status=MaintenanceOperationState.FAILED,
                accepted=False,
                executed=False,
                failure=_compaction_failure(exc, code="table_metadata_unavailable"),
                operation_id=operation_id,
                retry_safe=True,
            ).to_dict()

        plan = {
            "table_name": table_name,
            "sql": f"ALTER TABLE {quoted_table_name} EXECUTE optimize",
            "file_count": before_stats.get("file_count", 0),
            "snapshot_count": before_stats.get("snapshot_count", 0),
            "total_size_mb": before_stats.get("total_size_mb", 0.0),
            "concurrency_precondition": before_snapshot_id,
            "snapshot_guard": "provider_preflight_plus_iceberg_commit_conflict",
            "trino_boundary": "not_invoked" if dry_run else "pending",
        }
        if dry_run:
            return MaintenanceOperationResult(
                operation="compact",
                table_name=table_name,
                ref=branch,
                dry_run=True,
                status=MaintenanceOperationState.PLANNED,
                accepted=True,
                executed=False,
                before_snapshot_id=before_snapshot_id,
                planned=plan,
                evidence={
                    "before": {
                        "snapshot_id": before_snapshot_id,
                        "file_count": before_stats.get("file_count", 0),
                        "snapshot_count": before_stats.get("snapshot_count", 0),
                    }
                },
                operation_id=operation_id,
                retry_safe=True,
            ).to_dict()

        expected = (
            int(expected_snapshot_id) if expected_snapshot_id is not None else before_snapshot_id
        )
        if before_snapshot_id != expected:
            return _blocked_compaction_result(
                table_name=table_name,
                ref=branch,
                operation_id=operation_id,
                before_snapshot_id=before_snapshot_id,
                plan=plan,
                code="concurrent_change_detected",
                message="The table changed after the compaction plan; obtain a fresh dry-run.",
                details={
                    "expected_snapshot_id": expected,
                    "current_snapshot_id": before_snapshot_id,
                },
            )

        current_snapshot_id, current_stats = self._compaction_metadata(table_name, branch)
        if current_snapshot_id != expected:
            return _blocked_compaction_result(
                table_name=table_name,
                ref=branch,
                operation_id=operation_id,
                before_snapshot_id=current_snapshot_id,
                plan=plan,
                code="concurrent_change_detected",
                message="The table changed before executor execution; obtain a fresh dry-run.",
                details={
                    "expected_snapshot_id": expected,
                    "current_snapshot_id": current_snapshot_id,
                },
            )
        if executor is None:
            return MaintenanceOperationResult(
                operation="compact",
                table_name=table_name,
                ref=branch,
                dry_run=False,
                status=MaintenanceOperationState.FAILED,
                accepted=False,
                executed=False,
                before_snapshot_id=current_snapshot_id,
                planned=plan,
                failure={
                    "code": "maintenance_executor_required",
                    "type": "ConfigurationError",
                    "message": "Execute mode requires a ref-aware maintenance executor.",
                    "retryable": False,
                },
                operation_id=operation_id,
                retry_safe=True,
            ).to_dict()

        provider_result: dict[str, object] = {}
        try:
            raw_provider_result = executor.compact_iceberg_table(
                table_name=table_name,
                ref=branch,
                expected_snapshot_id=expected,
                operation_id=operation_id,
            )
            if isinstance(raw_provider_result, dict):
                provider_result = raw_provider_result
        except MaintenancePreconditionError as exc:
            return MaintenanceOperationResult(
                operation="compact",
                table_name=table_name,
                ref=branch,
                dry_run=False,
                status=MaintenanceOperationState.BLOCKED,
                accepted=False,
                executed=False,
                before_snapshot_id=current_snapshot_id,
                planned=plan,
                failure=_compaction_failure(exc, code="provider_precondition_failed"),
                operation_id=operation_id,
                retry_safe=True,
            ).to_dict()
        except MaintenanceExecutionError as exc:
            failure = _compaction_failure(
                exc.cause,
                code=(
                    "maintenance_preflight_failed"
                    if exc.phase is MaintenanceExecutionPhase.PREFLIGHT
                    else "maintenance_outcome_unknown"
                ),
                retryable=(None if exc.phase is MaintenanceExecutionPhase.PREFLIGHT else False),
            )
            failure.update(
                phase=exc.phase.value,
                outcome=(
                    "not_submitted"
                    if exc.phase is MaintenanceExecutionPhase.PREFLIGHT
                    else "unknown"
                ),
            )
            preflight_failed = exc.phase is MaintenanceExecutionPhase.PREFLIGHT
            return MaintenanceOperationResult(
                operation="compact",
                table_name=table_name,
                ref=branch,
                dry_run=False,
                status=MaintenanceOperationState.FAILED,
                accepted=not preflight_failed,
                executed=not preflight_failed,
                before_snapshot_id=current_snapshot_id,
                planned=plan,
                failure=failure,
                operation_id=operation_id,
                retry_safe=preflight_failed,
            ).to_dict()
        except Exception as exc:  # noqa: BLE001 - provider may have committed before the error surfaced
            return MaintenanceOperationResult(
                operation="compact",
                table_name=table_name,
                ref=branch,
                dry_run=False,
                status=MaintenanceOperationState.FAILED,
                accepted=True,
                executed=True,
                before_snapshot_id=current_snapshot_id,
                planned=plan,
                failure=_compaction_failure(
                    exc,
                    code="maintenance_outcome_unknown",
                    retryable=False,
                ),
                operation_id=operation_id,
                retry_safe=False,
            ).to_dict()

        try:
            after_snapshot_id, after_stats = self._compaction_metadata(table_name, branch)
        except Exception as exc:  # noqa: BLE001 - the commit may have succeeded
            return MaintenanceOperationResult(
                operation="compact",
                table_name=table_name,
                ref=branch,
                dry_run=False,
                status=MaintenanceOperationState.FAILED,
                accepted=True,
                executed=True,
                before_snapshot_id=current_snapshot_id,
                planned=plan,
                failure=_compaction_failure(
                    exc,
                    code="maintenance_outcome_unknown",
                    retryable=False,
                ),
                operation_id=operation_id,
                retry_safe=False,
            ).to_dict()

        changed = after_snapshot_id != current_snapshot_id
        return MaintenanceOperationResult(
            operation="compact",
            table_name=table_name,
            ref=branch,
            dry_run=False,
            status=(
                MaintenanceOperationState.SUCCEEDED if changed else MaintenanceOperationState.NOOP
            ),
            accepted=True,
            executed=True,
            before_snapshot_id=current_snapshot_id,
            after_snapshot_id=after_snapshot_id,
            planned={**plan, "trino_boundary": "executed"},
            affected={
                "snapshot_changed": changed,
                "file_count_before": current_stats.get("file_count", 0),
                "file_count_after": after_stats.get("file_count", 0),
                "total_size_mb_before": current_stats.get("total_size_mb", 0.0),
                "total_size_mb_after": after_stats.get("total_size_mb", 0.0),
            },
            evidence={
                "provider": {
                    "catalog": provider_result.get("catalog"),
                    "ref": provider_result.get("ref", branch),
                    "sql": provider_result.get("sql"),
                },
                "before": {
                    "snapshot_id": current_snapshot_id,
                    "snapshot_count": current_stats.get("snapshot_count", 0),
                    "file_count": current_stats.get("file_count", 0),
                },
                "after": {
                    "snapshot_id": after_snapshot_id,
                    "snapshot_count": after_stats.get("snapshot_count", 0),
                    "file_count": after_stats.get("file_count", 0),
                },
            },
            operation_id=operation_id,
            retry_safe=True,
        ).to_dict()

    def _compaction_metadata(self, table_name: str, ref: str) -> tuple[int | None, dict[str, Any]]:
        """Load the current Iceberg snapshot and file statistics for preconditions."""
        table = self.get_catalog(override_ref=ref).load_table(table_name)
        snapshot = table.current_snapshot()
        snapshot_id = int(snapshot.snapshot_id) if snapshot is not None else None
        stats = get_table_stats(table_name=table_name, ref=ref, table=table)
        if stats.get("current_snapshot_id") != snapshot_id:
            raise MaintenancePreconditionError(
                "Iceberg metadata returned inconsistent snapshot evidence"
            )
        return snapshot_id, stats

    def list_snapshots(self, *, table_name: str, limit: int = 10) -> list[dict]:
        """List recent table snapshots.

        Retrieves snapshot metadata including operation type, timestamp, and
        summary statistics. Results are sorted by timestamp (most recent first).

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            limit: Maximum number of snapshots to return (default: 10).

        Returns:
            list[dict]: Snapshot metadata dicts, most recent first. Each dict
                contains ``snapshot_id``, ``timestamp_ms``, ``operation``, and
                ``summary`` fields.

        Example:
            Review table history::

                snapshots = iceberg.list_snapshots(
                    table_name="raw.events",
                    limit=5
                )
                for snap in snapshots:
                    print(f"{snap['snapshot_id']}: {snap['operation']}")

        """
        return list_table_snapshots(table_name=table_name, limit=limit, ref=self.ref)

    def rollback_to_snapshot(self, *, table_name: str, snapshot_id: int | str) -> dict:
        """Roll back a table to a previous snapshot.

        Restores the table to a specific point in time using the snapshot ID.
        Creates a new snapshot that points to the historical state.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            snapshot_id: Target snapshot ID (can be int or string).

        Returns:
            dict: Rollback result containing ``rolled_back_to`` snapshot ID.

        Raises:
            Exception: Re-raises any errors during rollback.

        Example:
            Rollback after bad data load::

                # Find snapshot to restore
                snapshots = iceberg.list_snapshots(table_name="raw.events", limit=10)
                target_id = snapshots[1]["snapshot_id"]  # Previous snapshot

                # Rollback
                result = iceberg.rollback_to_snapshot(
                    table_name="raw.events",
                    snapshot_id=target_id
                )
                print(f"Rolled back to snapshot {result['rolled_back_to']}")

        Warning:
            Rollback creates a new snapshot. The newer snapshots are not
            deleted and can still be accessed if needed.

        """
        logger.info(
            "iceberg_resource_rollback_requested",
            table_name=table_name,
            snapshot_id=snapshot_id,
        )
        try:
            result = rollback_table_to_snapshot(
                table_name=table_name, snapshot_id=int(snapshot_id), ref=self.ref
            )
        except Exception as exc:
            logger.error(
                "iceberg_resource_rollback_failed",
                table_name=table_name,
                snapshot_id=snapshot_id,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "iceberg_resource_rollback_completed",
            table_name=table_name,
            snapshot_id=snapshot_id,
        )
        return result

    def vacuum(self, *, table_name: str, retain_hours: int = 168) -> dict:
        """Remove expired snapshots and orphan files.

        Performs table maintenance by:
        1. Expiring snapshots older than the retention period
        2. Removing orphan files not referenced by any remaining snapshot

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            retain_hours: Retention period in hours (default: 168 = 7 days).
                Snapshots newer than this will be retained.

        Returns:
            dict: Maintenance results containing:
                - ``deleted_snapshots``: Number of expired snapshots removed.
                - ``orphan_files_removed``: Number of orphan files deleted.

        Raises:
            Exception: Re-raises any errors during maintenance.

        Example:
            Weekly maintenance::

                result = iceberg.vacuum(
                    table_name="raw.events",
                    retain_hours=168  # Keep 7 days
                )
                print(f"Removed {result['deleted_snapshots']} snapshots")
                print(f"Removed {result['orphan_files_removed']} orphan files")

        Warning:
            Orphan file removal permanently deletes data files from storage.
            Ensure no concurrent writes are happening during vacuum operations.

        """
        logger.info(
            "iceberg_resource_vacuum_requested",
            table_name=table_name,
            retain_hours=retain_hours,
        )
        snap_result = expire_snapshots(
            table_name=table_name, older_than_hours=retain_hours, ref=self.ref
        )
        orphan_result = remove_orphan_files(
            table_name=table_name, older_than_hours=retain_hours, dry_run=False, ref=self.ref
        )
        result = {
            "deleted_snapshots": snap_result["deleted_snapshots"],
            "orphan_files_removed": orphan_result["orphan_count"],
        }
        logger.info(
            "iceberg_resource_vacuum_completed",
            table_name=table_name,
            **result,
        )
        return result
