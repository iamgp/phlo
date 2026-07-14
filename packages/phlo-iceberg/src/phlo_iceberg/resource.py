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
from datetime import UTC, datetime, timedelta
import hashlib
import json
import re
from typing import Any, cast
from urllib.parse import urlsplit

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
    get_table_stats,
    list_table_snapshots,
    merge_to_table,
    overwrite_table,
    rollback_table_to_snapshot,
)

logger = get_logger(__name__)

_COMPACTION_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SAFE_MIN_RETENTION_HOURS = 7 * 24
DEFAULT_MAX_AFFECTED_OBJECTS = 1_000
DEFAULT_MAX_AFFECTED_BYTES = 10 * 1024 * 1024 * 1024


def _validate_compaction_table_name(table_name: str) -> str:
    """Validate and quote the namespace.table relation used by Trino."""
    parts = table_name.split(".")
    if len(parts) != 2 or any(not _COMPACTION_IDENTIFIER.fullmatch(part) for part in parts):
        raise ValueError(
            "Compaction table_name must be a namespace.table identifier containing only "
            "letters, numbers, and underscores."
        )
    return ".".join(f'"{part}"' for part in parts)


def _maintenance_plan_token(plan: dict[str, object]) -> str:
    """Hash only plan fields that change the requested mutation."""
    basis = json.loads(json.dumps(plan, sort_keys=True, default=str))
    for key in ("plan_token", "observed_at_ms", "age_seconds", "trino_boundary"):
        _remove_plan_field(basis, key)
    encoded = json.dumps(basis, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _remove_plan_field(value: object, key: str) -> None:
    if isinstance(value, dict):
        mapping = cast(dict[str, Any], value)
        mapping.pop(key, None)
        for child in mapping.values():
            _remove_plan_field(child, key)
    elif isinstance(value, list):
        for child in value:
            _remove_plan_field(child, key)


def _retention_threshold(hours: int) -> str:
    if hours % 24 == 0:
        return f"{hours // 24}d"
    return f"{hours}h"


def _snapshot_id(snapshot: object) -> int:
    return int(getattr(snapshot, "snapshot_id"))


def _snapshot_summary(snapshot: object) -> dict[str, object]:
    summary = getattr(snapshot, "summary", None)
    operation = getattr(getattr(summary, "operation", None), "value", None)
    return {"operation": operation, "summary": dict(getattr(summary, "additional_properties", {}))}


def _safe_file_size(file_info: object) -> int | None:
    for name in ("size_bytes", "file_size_in_bytes", "length", "size"):
        value = getattr(file_info, name, None)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
    return None


def _storage_path_key(path: str) -> str:
    """Normalize URI and PyArrow filesystem paths for reference comparison."""
    parsed = urlsplit(path)
    if parsed.scheme in {"s3", "s3a", "s3n"}:
        return f"{parsed.netloc}{parsed.path}".rstrip("/")
    return path.rstrip("/")


def _list_storage_files(io: object, location: str) -> list[Any]:
    """List files through PyIceberg's configured PyArrow filesystem."""
    from pyarrow.fs import FileSelector, FileType

    parse_location = getattr(io, "parse_location", None)
    fs_by_scheme = getattr(io, "fs_by_scheme", None)
    if not callable(parse_location) or not callable(fs_by_scheme):
        raise MaintenancePreconditionError(
            "Configured Iceberg FileIO cannot provide a safe recursive object listing."
        )
    scheme, netloc, path = parse_location(location, getattr(io, "properties", {}))
    filesystem = fs_by_scheme(scheme, netloc)
    infos = filesystem.get_file_info(FileSelector(path, recursive=True, allow_not_found=False))
    return [info for info in infos if getattr(info, "type", None) is FileType.File]


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


def _retention_metadata_failure_result(
    *,
    operation: str,
    table_name: str,
    ref: str,
    dry_run: bool,
    exc: Exception,
    code: str,
    operation_id: str | None,
) -> dict[str, object]:
    """Return metadata failure evidence with one authoritative retry classification."""
    failure = _compaction_failure(exc, code=code)
    retry_safe = failure.get("retryable") is True
    return MaintenanceOperationResult(
        operation=operation,
        table_name=table_name,
        ref=ref,
        dry_run=dry_run,
        status=MaintenanceOperationState.FAILED,
        accepted=False,
        executed=False,
        failure=failure,
        operation_id=operation_id,
        retry_safe=retry_safe,
    ).to_dict()


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
    return _serialize_compaction_result(
        MaintenanceOperationResult(
            operation="compact",
            table_name=table_name,
            ref=ref,
            dry_run=False,
            status=MaintenanceOperationState.BLOCKED,
            accepted=False,
            executed=False,
            before_revision=before_snapshot_id,
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
        )
    )


def _serialize_compaction_result(result: MaintenanceOperationResult) -> dict[str, object]:
    """Add Iceberg snapshot aliases without widening the core result contract."""
    payload = result.to_dict()
    if result.before_revision is not None:
        payload["before_snapshot_id"] = result.before_revision
    if result.after_revision is not None:
        payload["after_snapshot_id"] = result.after_revision
    return payload


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
            supports_vacuum=False,
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

    def list_tables(self, *, namespace: str, ref: str) -> list[str]:
        """List fully qualified tables through the provider's catalog."""
        tables = self.get_catalog(override_ref=ref).list_tables(namespace)
        return [f"{namespace}.{table[1]}" for table in tables]

    def list_namespaces(self, *, ref: str) -> list[str]:
        """List namespaces through the provider's catalog."""
        return [namespace[0] for namespace in self.get_catalog(override_ref=ref).list_namespaces()]

    def get_table_stats(self, *, table_name: str, ref: str) -> dict[str, Any]:
        """Return normalized table statistics through the provider boundary."""
        return get_table_stats(table_name=table_name, ref=ref)

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
        expected_revision: str | int | None = None,
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
            expected_revision: Provider-neutral revision token observed by the caller.
            expected_snapshot_id: Snapshot observed by the caller. When omitted,
                execute mode captures and rechecks the current snapshot itself. This
                provider-specific alias is retained for compatibility.
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
            return _serialize_compaction_result(
                MaintenanceOperationResult(
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
                )
            )

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
            return _serialize_compaction_result(
                MaintenanceOperationResult(
                    operation="compact",
                    table_name=table_name,
                    ref=branch,
                    dry_run=True,
                    status=MaintenanceOperationState.PLANNED,
                    accepted=True,
                    executed=False,
                    before_revision=before_snapshot_id,
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
                )
            )

        if (
            expected_revision is not None
            and expected_snapshot_id is not None
            and int(expected_revision) != int(expected_snapshot_id)
        ):
            raise ValueError("expected_revision and expected_snapshot_id must match")
        expected_token = (
            expected_revision if expected_revision is not None else expected_snapshot_id
        )
        expected = int(expected_token) if expected_token is not None else before_snapshot_id
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
            return _serialize_compaction_result(
                MaintenanceOperationResult(
                    operation="compact",
                    table_name=table_name,
                    ref=branch,
                    dry_run=False,
                    status=MaintenanceOperationState.FAILED,
                    accepted=False,
                    executed=False,
                    before_revision=current_snapshot_id,
                    planned=plan,
                    failure={
                        "code": "maintenance_executor_required",
                        "type": "ConfigurationError",
                        "message": "Execute mode requires a ref-aware maintenance executor.",
                        "retryable": False,
                    },
                    operation_id=operation_id,
                    retry_safe=True,
                )
            )

        provider_result: dict[str, object] = {}
        try:
            raw_provider_result = executor.compact_table(
                table_name=table_name,
                ref=branch,
                expected_revision=expected,
                operation_id=operation_id,
            )
            if isinstance(raw_provider_result, dict):
                provider_result = raw_provider_result
        except MaintenancePreconditionError as exc:
            return _serialize_compaction_result(
                MaintenanceOperationResult(
                    operation="compact",
                    table_name=table_name,
                    ref=branch,
                    dry_run=False,
                    status=MaintenanceOperationState.BLOCKED,
                    accepted=False,
                    executed=False,
                    before_revision=current_snapshot_id,
                    planned=plan,
                    failure=_compaction_failure(exc, code="provider_precondition_failed"),
                    operation_id=operation_id,
                    retry_safe=True,
                )
            )
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
            return _serialize_compaction_result(
                MaintenanceOperationResult(
                    operation="compact",
                    table_name=table_name,
                    ref=branch,
                    dry_run=False,
                    status=MaintenanceOperationState.FAILED,
                    accepted=not preflight_failed,
                    executed=not preflight_failed,
                    before_revision=current_snapshot_id,
                    planned=plan,
                    failure=failure,
                    operation_id=operation_id,
                    retry_safe=preflight_failed,
                )
            )
        except Exception as exc:  # noqa: BLE001 - provider may have committed before the error surfaced
            return _serialize_compaction_result(
                MaintenanceOperationResult(
                    operation="compact",
                    table_name=table_name,
                    ref=branch,
                    dry_run=False,
                    status=MaintenanceOperationState.FAILED,
                    accepted=True,
                    executed=True,
                    before_revision=current_snapshot_id,
                    planned=plan,
                    failure=_compaction_failure(
                        exc,
                        code="maintenance_outcome_unknown",
                        retryable=False,
                    ),
                    operation_id=operation_id,
                    retry_safe=False,
                )
            )

        try:
            after_snapshot_id, after_stats = self._compaction_metadata(table_name, branch)
        except Exception as exc:  # noqa: BLE001 - the commit may have succeeded
            return _serialize_compaction_result(
                MaintenanceOperationResult(
                    operation="compact",
                    table_name=table_name,
                    ref=branch,
                    dry_run=False,
                    status=MaintenanceOperationState.FAILED,
                    accepted=True,
                    executed=True,
                    before_revision=current_snapshot_id,
                    planned=plan,
                    failure=_compaction_failure(
                        exc,
                        code="maintenance_outcome_unknown",
                        retryable=False,
                    ),
                    operation_id=operation_id,
                    retry_safe=False,
                )
            )

        changed = after_snapshot_id != current_snapshot_id
        return _serialize_compaction_result(
            MaintenanceOperationResult(
                operation="compact",
                table_name=table_name,
                ref=branch,
                dry_run=False,
                status=(
                    MaintenanceOperationState.SUCCEEDED
                    if changed
                    else MaintenanceOperationState.NOOP
                ),
                accepted=True,
                executed=True,
                before_revision=current_snapshot_id,
                after_revision=after_snapshot_id,
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
            )
        )

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

    def _retention_metadata(
        self,
        *,
        table_name: str,
        ref: str,
        retention_hours: int,
        retain_last: int,
        operation: str,
        catalog: str | None,
        max_affected_objects: int | None,
        max_affected_bytes: int | None,
    ) -> tuple[dict[str, object], object]:
        """Build a provider-independent snapshot-retention plan."""
        table = self.get_catalog(override_ref=ref).load_table(table_name)
        snapshots = sorted(
            list(table.snapshots()),
            key=lambda snapshot: int(getattr(snapshot, "timestamp_ms", 0)),
            reverse=True,
        )
        current = table.current_snapshot()
        current_snapshot_id = int(current.snapshot_id) if current is not None else None
        stats = get_table_stats(table_name=table_name, ref=ref, table=table)
        if stats.get("current_snapshot_id") != current_snapshot_id:
            raise MaintenancePreconditionError(
                "Iceberg metadata returned inconsistent snapshot evidence"
            )
        refs_available = True
        refs: dict[str, int] = {}
        try:
            for name, snapshot_ref in table.refs().items():
                snapshot_id = getattr(snapshot_ref, "snapshot_id", None)
                if snapshot_id is not None:
                    refs[str(name)] = int(snapshot_id)
        except Exception:
            refs_available = False
        protected_ids = set(refs.values())
        if current_snapshot_id is not None:
            protected_ids.add(current_snapshot_id)
        protected_ids.update(
            _snapshot_id(snapshot) for snapshot in snapshots[: max(retain_last, 1)]
        )
        cutoff_ms = int((datetime.now(UTC) - timedelta(hours=retention_hours)).timestamp() * 1000)
        candidates: list[dict[str, object]] = []
        for snapshot in snapshots:
            snapshot_id = _snapshot_id(snapshot)
            timestamp_ms = int(getattr(snapshot, "timestamp_ms", 0))
            age_seconds = max(0.0, (datetime.now(UTC).timestamp() * 1000 - timestamp_ms) / 1000)
            if timestamp_ms < cutoff_ms and snapshot_id not in protected_ids:
                candidates.append(
                    {
                        "snapshot_id": snapshot_id,
                        "timestamp_ms": timestamp_ms,
                        "age_seconds": round(age_seconds, 3),
                        **_snapshot_summary(snapshot),
                    }
                )
        candidate_ids: set[int] = set()
        affected_bytes: int | None = 0 if not candidates else None
        unavailable_fields: list[str] = []
        if candidates:
            try:
                candidate_ids = {
                    int(cast(dict[str, Any], candidate)["snapshot_id"]) for candidate in candidates
                }
                candidate_paths: dict[str, int | None] = {}
                retained_paths: set[str] = set()
                for snapshot in snapshots:
                    snapshot_id = _snapshot_id(snapshot)
                    for manifest in snapshot.manifests(table.io):
                        for entry in manifest.fetch_manifest_entry(table.io):
                            data_file = entry.data_file
                            path = str(data_file.file_path)
                            size = _safe_file_size(data_file)
                            if snapshot_id in candidate_ids:
                                candidate_paths[path] = size
                            else:
                                retained_paths.add(path)
                unreferenced = set(candidate_paths) - retained_paths
                sizes = [candidate_paths[path] for path in unreferenced]
                if any(size is None for size in sizes):
                    unavailable_fields.append("affected_bytes")
                else:
                    affected_bytes = sum(int(size) for size in sizes if size is not None)
            except Exception:
                unavailable_fields.append("affected_bytes")
        plan: dict[str, object] = {
            "operation": operation,
            "table_name": table_name,
            "ref": ref,
            "catalog": catalog,
            "retention_hours": retention_hours,
            "retention_threshold": _retention_threshold(retention_hours),
            "minimum_safe_retention_hours": SAFE_MIN_RETENTION_HOURS,
            "retain_last": retain_last,
            "count_retention": (
                "requested_provider_479_plus" if retain_last > 1 else "not_requested"
            ),
            "provider_version": None,
            "before_snapshot_id": current_snapshot_id,
            "snapshot_count": len(snapshots),
            "file_count": stats.get("file_count"),
            "total_size_bytes": stats.get("total_size_bytes"),
            "candidate_snapshots": candidates,
            "retained_snapshot_ids": [
                _snapshot_id(snapshot)
                for snapshot in snapshots
                if _snapshot_id(snapshot) not in candidate_ids
            ],
            "protected_snapshot_ids": sorted(protected_ids),
            "table_snapshot_refs": refs,
            "table_snapshot_ref_evidence": "available" if refs_available else "unavailable",
            "nessie_ref_evidence": "unavailable",
            "affected_objects": len(candidates),
            "affected_objects_scope": "candidate_snapshots_only",
            "affected_bytes": affected_bytes,
            "affected_bytes_scope": (
                "observed_unreferenced_data_files_only; evidence_not_deletion_ceiling"
            ),
            "limits_scope": (
                "candidate_snapshot_count_only; provider_metadata_and_data_files_excluded"
            ),
            "limits_enforced": False,
            "deletion_surface": "provider_threshold_not_bound",
            "unavailable_fields": [*unavailable_fields, "provider_version"],
            "max_affected_objects": max_affected_objects,
            "max_affected_bytes": max_affected_bytes,
            "snapshot_guard": "fresh_table_metadata_only",
            "trino_boundary": "pending",
            "execution_support": "unsupported_without_bound_deletion_set",
            "observed_at_ms": int(datetime.now(UTC).timestamp() * 1000),
        }
        plan["plan_token"] = _maintenance_plan_token(plan)
        return plan, table

    def _orphan_retention_metadata(
        self,
        *,
        table_name: str,
        ref: str,
        retention_hours: int,
        catalog: str | None,
        max_affected_objects: int | None,
        max_affected_bytes: int | None,
    ) -> tuple[dict[str, object], object]:
        """Build an orphan plan without invoking Trino."""
        table = self.get_catalog(override_ref=ref).load_table(table_name)
        current = table.current_snapshot()
        current_snapshot_id = int(current.snapshot_id) if current is not None else None
        stats = get_table_stats(table_name=table_name, ref=ref, table=table)
        if stats.get("current_snapshot_id") != current_snapshot_id:
            raise MaintenancePreconditionError(
                "Iceberg metadata returned inconsistent snapshot evidence"
            )
        refs_available = True
        refs: dict[str, int] = {}
        try:
            for name, snapshot_ref in table.refs().items():
                snapshot_id = getattr(snapshot_ref, "snapshot_id", None)
                if snapshot_id is not None:
                    refs[str(name)] = int(snapshot_id)
        except Exception:
            refs_available = False
        referenced_files: set[str] = set()
        for snapshot in table.snapshots():
            for manifest in snapshot.manifests(table.io):
                referenced_files.add(str(manifest.manifest_path))
                for entry in manifest.fetch_manifest_entry(table.io):
                    referenced_files.add(str(entry.data_file.file_path))
        cutoff = datetime.now(UTC) - timedelta(hours=retention_hours)
        candidates: list[dict[str, object]] = []
        unavailable_fields: list[str] = []
        scan_status = "available"
        try:
            normalized_references = {_storage_path_key(path) for path in referenced_files}
            for file_info in _list_storage_files(table.io, f"{table.location()}/data"):
                path = str(file_info.path)
                if _storage_path_key(path) in normalized_references:
                    continue
                mtime = getattr(file_info, "mtime", None)
                if isinstance(mtime, datetime):
                    mtime_value = mtime if mtime.tzinfo else mtime.replace(tzinfo=UTC)
                elif mtime is not None:
                    mtime_value = datetime.fromtimestamp(float(mtime), tz=UTC)
                else:
                    unavailable_fields.append("candidate_age")
                    continue
                if mtime_value < cutoff:
                    candidates.append(
                        {
                            "path": path,
                            "mtime": mtime_value.isoformat(),
                            "age_seconds": round(
                                (datetime.now(UTC) - mtime_value).total_seconds(), 3
                            ),
                            "size_bytes": _safe_file_size(file_info),
                        }
                    )
        except Exception as exc:  # noqa: BLE001 - fail closed on destructive scans
            scan_status = "unavailable"
            unavailable_fields.append(f"candidate_listing: {type(exc).__name__}")
        sizes = [cast(int | None, candidate.get("size_bytes")) for candidate in candidates]
        if any(size is None for size in sizes):
            affected_bytes = None if candidates else 0
            if candidates:
                unavailable_fields.append("affected_bytes")
        else:
            affected_bytes = sum(int(size) for size in sizes if size is not None)
        plan: dict[str, object] = {
            "operation": "cleanup_orphan_files",
            "table_name": table_name,
            "ref": ref,
            "catalog": catalog,
            "retention_hours": retention_hours,
            "retention_threshold": _retention_threshold(retention_hours),
            "minimum_safe_retention_hours": SAFE_MIN_RETENTION_HOURS,
            "before_snapshot_id": current_snapshot_id,
            "snapshot_count": stats.get("snapshot_count"),
            "file_count": stats.get("file_count"),
            "total_size_bytes": stats.get("total_size_bytes"),
            "candidate_files": candidates,
            "retained_file_count": stats.get("file_count"),
            "retained_bytes": stats.get("total_size_bytes"),
            "protected_snapshot_ids": sorted({current_snapshot_id, *refs.values()} - {None}),
            "table_snapshot_refs": refs,
            "table_snapshot_ref_evidence": "available" if refs_available else "unavailable",
            "nessie_ref_evidence": "unavailable",
            "scan_status": scan_status,
            "affected_objects": len(candidates),
            "affected_bytes": affected_bytes,
            "limits_scope": ("candidate_orphan_files; provider_internal_metadata_not_counted"),
            "limits_enforced": False,
            "deletion_surface": "provider_threshold_not_bound",
            "max_affected_objects": max_affected_objects,
            "max_affected_bytes": max_affected_bytes,
            "snapshot_guard": "fresh_table_metadata_only",
            "trino_boundary": "pending",
            "execution_support": "unsupported_without_bound_deletion_set",
            "observed_at_ms": int(datetime.now(UTC).timestamp() * 1000),
            "unavailable_fields": sorted(set(unavailable_fields)),
        }
        plan["plan_token"] = _maintenance_plan_token(plan)
        return plan, table

    def _retention_blocked(
        self,
        *,
        operation: str,
        table_name: str,
        ref: str,
        dry_run: bool,
        plan: dict[str, object],
        code: str,
        message: str,
        operation_id: str | None,
        retry_safe: bool = True,
    ) -> dict[str, object]:
        before_snapshot_id = plan.get("before_snapshot_id")
        before_snapshot = (
            int(before_snapshot_id) if isinstance(before_snapshot_id, (int, str)) else None
        )
        return MaintenanceOperationResult(
            operation=operation,
            table_name=table_name,
            ref=ref,
            dry_run=dry_run,
            status=MaintenanceOperationState.BLOCKED,
            accepted=False,
            executed=False,
            before_revision=before_snapshot,
            planned=plan,
            evidence={"before": plan, "unavailable_fields": plan.get("unavailable_fields", [])},
            failure={
                "code": code,
                "type": "PreconditionError",
                "message": message,
                "retryable": retry_safe,
            },
            operation_id=operation_id,
            plan_token=str(plan.get("plan_token")),
            retry_safe=retry_safe,
        ).to_dict()

    def _validate_retention_execute(
        self,
        *,
        operation: str,
        table_name: str,
        ref: str,
        catalog: str | None,
        plan: dict[str, object],
        expected_snapshot_id: int | str | None,
        confirmation_token: str | None,
        max_affected_objects: int | None,
        max_affected_bytes: int | None,
        operation_id: str | None,
    ) -> dict[str, object]:
        """Validate an execute request and return a blocked result.

        The v1 provider boundary has no operation that can bind the complete
        planned deletion surface, so this method deliberately never submits SQL.
        """
        plan = cast(dict[str, Any], plan)
        plan_token = str(plan["plan_token"])

        def block(code: str, message: str, *, retry_safe: bool = True) -> dict[str, object]:
            return self._retention_blocked(
                operation=operation,
                table_name=table_name,
                ref=ref,
                dry_run=False,
                plan={**plan, "trino_boundary": "not_invoked"},
                code=code,
                message=message,
                operation_id=operation_id,
                retry_safe=retry_safe,
            )

        if not catalog:
            return block("catalog_required", "Execute mode requires an explicit catalog.")
        if expected_snapshot_id is None:
            return block(
                "snapshot_precondition_required",
                "Execute mode requires the snapshot observed by the plan.",
            )
        if not confirmation_token or confirmation_token != plan_token:
            return block(
                "plan_token_invalid", "Confirmation token does not match this exact current plan."
            )
        if max_affected_objects is None or max_affected_bytes is None:
            return block(
                "safety_limits_required", "Execute mode requires finite object and byte limits."
            )
        if max_affected_objects < 0 or max_affected_bytes < 0:
            return block("invalid_safety_limit", "Safety limits must be non-negative.")
        if int(plan.get("affected_objects") or 0) > max_affected_objects:
            return block(
                "affected_object_limit_exceeded",
                "The plan exceeds max_affected_objects; obtain a narrower plan.",
            )
        if plan.get("affected_bytes") is None and int(plan.get("affected_objects") or 0):
            return block(
                "affected_bytes_unavailable", "The provider cannot prove the affected bytes safely."
            )
        if int(plan.get("affected_bytes") or 0) > max_affected_bytes:
            return block(
                "affected_byte_limit_exceeded",
                "The plan exceeds max_affected_bytes; obtain a narrower plan.",
            )
        if plan.get("table_snapshot_ref_evidence") != "available":
            return block(
                "table_snapshot_ref_evidence_unavailable",
                "Table snapshot-reference evidence is unavailable; deletion is refused.",
            )
        if plan.get("scan_status") == "unavailable":
            return block(
                "orphan_scan_unavailable", "The orphan scan did not complete; deletion is refused."
            )
        try:
            expected = int(expected_snapshot_id)
        except (TypeError, ValueError):
            return block(
                "invalid_snapshot_precondition", "expected_snapshot_id must be an integer."
            )
        if expected != plan.get("before_snapshot_id"):
            return block(
                "concurrent_change_detected",
                "The table changed after planning; obtain a fresh dry-run.",
            )
        return self._retention_blocked(
            operation=operation,
            table_name=table_name,
            ref=ref,
            dry_run=False,
            plan={**plan, "trino_boundary": "not_invoked"},
            code="bounded_execution_unsupported",
            message=(
                "The Trino retention procedure accepts only a threshold and cannot bind "
                "the provider deletion surface to this exact candidate and byte plan."
            ),
            operation_id=operation_id,
            retry_safe=False,
        )

    def expire_snapshots(
        self,
        *,
        table_name: str,
        override_ref: str | None = None,
        catalog: str | None = None,
        dry_run: bool = True,
        retention_hours: int = SAFE_MIN_RETENTION_HOURS,
        retain_last: int = 5,
        minimum_retention_hours: int = SAFE_MIN_RETENTION_HOURS,
        expected_snapshot_id: int | str | None = None,
        confirmation_token: str | None = None,
        max_affected_objects: int | None = None,
        max_affected_bytes: int | None = None,
        operation_id: str | None = None,
    ) -> dict[str, object]:
        """Plan or execute guarded provider-neutral snapshot expiry."""
        branch = override_ref or self.ref
        _validate_compaction_table_name(table_name)
        effective_minimum = max(minimum_retention_hours, SAFE_MIN_RETENTION_HOURS)
        if retention_hours < effective_minimum or retain_last < 1:
            plan: dict[str, object] = {
                "operation": "expire_snapshots",
                "table_name": table_name,
                "ref": branch,
                "catalog": catalog,
                "retention_hours": retention_hours,
                "minimum_safe_retention_hours": effective_minimum,
                "retain_last": retain_last,
                "unavailable_fields": [],
            }
            plan["plan_token"] = _maintenance_plan_token(plan)
            return self._retention_blocked(
                operation="expire_snapshots",
                table_name=table_name,
                ref=branch,
                dry_run=dry_run,
                plan=plan,
                code="retention_floor_violation",
                message="Retention cannot be weakened below the safe production floor.",
                operation_id=operation_id,
            )
        try:
            plan, _ = self._retention_metadata(
                table_name=table_name,
                ref=branch,
                retention_hours=retention_hours,
                retain_last=retain_last,
                operation="expire_snapshots",
                catalog=catalog,
                max_affected_objects=max_affected_objects,
                max_affected_bytes=max_affected_bytes,
            )
        except Exception as exc:
            return _retention_metadata_failure_result(
                operation="expire_snapshots",
                table_name=table_name,
                ref=branch,
                dry_run=dry_run,
                exc=exc,
                code="table_metadata_unavailable",
                operation_id=operation_id,
            )
        plan = cast(dict[str, Any], plan)
        if dry_run:
            return MaintenanceOperationResult(
                operation="expire_snapshots",
                table_name=table_name,
                ref=branch,
                dry_run=True,
                status=(
                    MaintenanceOperationState.NOOP
                    if not plan["candidate_snapshots"]
                    else MaintenanceOperationState.PLANNED
                ),
                accepted=True,
                executed=False,
                before_revision=plan.get("before_snapshot_id"),
                planned={**plan, "trino_boundary": "not_invoked"},
                evidence={"before": plan},
                operation_id=operation_id,
                plan_token=str(plan["plan_token"]),
                retry_safe=True,
            ).to_dict()
        return self._validate_retention_execute(
            operation="expire_snapshots",
            table_name=table_name,
            ref=branch,
            catalog=catalog,
            plan=plan,
            expected_snapshot_id=expected_snapshot_id,
            confirmation_token=confirmation_token,
            max_affected_objects=max_affected_objects,
            max_affected_bytes=max_affected_bytes,
            operation_id=operation_id,
        )

    def cleanup_orphan_files(
        self,
        *,
        table_name: str,
        override_ref: str | None = None,
        catalog: str | None = None,
        dry_run: bool = True,
        retention_hours: int = SAFE_MIN_RETENTION_HOURS,
        minimum_retention_hours: int = SAFE_MIN_RETENTION_HOURS,
        expected_snapshot_id: int | str | None = None,
        confirmation_token: str | None = None,
        max_affected_objects: int | None = None,
        max_affected_bytes: int | None = None,
        operation_id: str | None = None,
    ) -> dict[str, object]:
        """Plan or execute guarded provider-neutral orphan-file cleanup."""
        branch = override_ref or self.ref
        _validate_compaction_table_name(table_name)
        effective_minimum = max(minimum_retention_hours, SAFE_MIN_RETENTION_HOURS)
        if retention_hours < effective_minimum:
            plan: dict[str, object] = {
                "operation": "cleanup_orphan_files",
                "table_name": table_name,
                "ref": branch,
                "catalog": catalog,
                "retention_hours": retention_hours,
                "minimum_safe_retention_hours": effective_minimum,
                "unavailable_fields": [],
            }
            plan["plan_token"] = _maintenance_plan_token(plan)
            return self._retention_blocked(
                operation="cleanup_orphan_files",
                table_name=table_name,
                ref=branch,
                dry_run=dry_run,
                plan=plan,
                code="retention_floor_violation",
                message="Retention cannot be weakened below the safe production floor.",
                operation_id=operation_id,
            )
        try:
            plan, _ = self._orphan_retention_metadata(
                table_name=table_name,
                ref=branch,
                retention_hours=retention_hours,
                catalog=catalog,
                max_affected_objects=max_affected_objects,
                max_affected_bytes=max_affected_bytes,
            )
        except Exception as exc:
            return _retention_metadata_failure_result(
                operation="cleanup_orphan_files",
                table_name=table_name,
                ref=branch,
                dry_run=dry_run,
                exc=exc,
                code="orphan_scan_unavailable",
                operation_id=operation_id,
            )
        plan = cast(dict[str, Any], plan)
        if plan.get("scan_status") == "unavailable":
            return self._retention_blocked(
                operation="cleanup_orphan_files",
                table_name=table_name,
                ref=branch,
                dry_run=dry_run,
                plan={**plan, "trino_boundary": "not_invoked"},
                code="orphan_scan_unavailable",
                message=(
                    "The orphan discovery scan is unavailable; no complete candidate set "
                    "is available for this operation."
                ),
                operation_id=operation_id,
                retry_safe=True,
            )
        if dry_run:
            return MaintenanceOperationResult(
                operation="cleanup_orphan_files",
                table_name=table_name,
                ref=branch,
                dry_run=True,
                status=(
                    MaintenanceOperationState.NOOP
                    if not plan["candidate_files"]
                    else MaintenanceOperationState.PLANNED
                ),
                accepted=True,
                executed=False,
                before_revision=plan.get("before_snapshot_id"),
                planned={**plan, "trino_boundary": "not_invoked"},
                evidence={"before": plan},
                operation_id=operation_id,
                plan_token=str(plan["plan_token"]),
                retry_safe=True,
            ).to_dict()
        return self._validate_retention_execute(
            operation="cleanup_orphan_files",
            table_name=table_name,
            ref=branch,
            catalog=catalog,
            plan=plan,
            expected_snapshot_id=expected_snapshot_id,
            confirmation_token=confirmation_token,
            max_affected_objects=max_affected_objects,
            max_affected_bytes=max_affected_bytes,
            operation_id=operation_id,
        )

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

    def vacuum(
        self,
        *,
        table_name: str,
        retain_hours: int = SAFE_MIN_RETENTION_HOURS,
        dry_run: bool = True,
    ) -> dict[str, object]:
        """Plan both retention operations without bypassing their safety contract.

        Snapshot expiry and orphan deletion are separate provider procedures with
        separate snapshot fences, so this convenience method deliberately remains
        planning-only. Execute each returned plan independently with its own
        confirmation token.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            retain_hours: Retention period in hours (default: 168 = 7 days).
                Snapshots newer than this will be retained.

        Returns:
            dict: Independent snapshot-expiry and orphan-cleanup plans.

        Raises:
            Exception: Re-raises any errors during maintenance.

        Example:
            Weekly maintenance::

                result = iceberg.vacuum(
                    table_name="raw.events",
                    retain_hours=168  # Keep 7 days
                )
                print(result["expire_snapshots"]["plan_token"])

        """
        if not dry_run:
            raise MaintenancePreconditionError(
                "vacuum is planning-only; execute snapshot expiry and orphan cleanup "
                "separately with their exact plan tokens"
            )
        return {
            "expire_snapshots": self.expire_snapshots(
                table_name=table_name, retention_hours=retain_hours, dry_run=True
            ),
            "cleanup_orphan_files": self.cleanup_orphan_files(
                table_name=table_name, retention_hours=retain_hours, dry_run=True
            ),
        }
