"""Delta Lake resource wrapper for Phlo table store interface.

This module provides the DeltaResource class that wraps Delta Lake table
operations and integrates with the Phlo resource provider system. It handles
table lifecycle operations, data ingestion, and maintenance operations.

Example:
    from phlo_delta.resource import DeltaResource

    resource = DeltaResource()
    table = resource.get_table("raw.events")
    resource.append_parquet("raw.events", "/data/events.parquet")

Table-store adapter boundary: implements the TableStoreSupport contract from
phlo.capabilities.interfaces; no repository module imports it directly.
"""

from __future__ import annotations

import importlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, cast

import pyarrow as pa
from pandera.pandas import DataFrameModel

from phlo.capabilities.interfaces import TableStoreSupport
from phlo.exceptions import PhloConfigError
from phlo.logging import get_logger
from phlo_delta.settings import get_settings
from phlo_delta.tables import (
    append_to_table,
    delete_rows_from_table,
    ensure_table,
    list_table_versions,
    merge_to_table,
    overwrite_table,
    remove_orphan_files,
    rollback_table_to_version,
)

logger = get_logger(__name__)


def _load_delta_table() -> type[Any]:
    """Load the optional DeltaTable runtime only when needed.

    Lazily imports the DeltaTable class from the deltalake package
    to avoid import-time dependencies.

    Returns:
        type[Any]: The DeltaTable class.

    """
    return cast(Any, importlib.import_module("deltalake")).DeltaTable


def _resolve_delta_ref(override_ref: str | None) -> None:
    """Validate the requested override ref for Delta operations.

    Delta tables in Phlo are not branch-aware. Accept the default ``main`` ref
    for table-store interface compatibility and reject any branch-like override.

    Args:
        override_ref: Optional branch reference to validate.

    Raises:
        PhloConfigError: If an unsupported override_ref is provided.

    Example:
        _resolve_delta_ref(None)  # OK
        _resolve_delta_ref("main")  # OK
        _resolve_delta_ref("dev")  # Raises PhloConfigError

    """
    if override_ref in (None, "", "main"):
        return
    raise PhloConfigError(
        message=f"Delta table_store does not support refs; got override_ref={override_ref!r}",
        suggestions=[
            "Use the default main ref when writing to Delta tables",
            "Use resource.support.supports_refs to branch behaviour before calling table-store operations",
            "Use phlo-iceberg if you need Nessie branch-aware table writes",
        ],
    )


def _partition_columns_from_spec(
    partition_spec: Sequence[tuple[str, str] | str] | None,
) -> list[str] | None:
    """Convert shared partition_spec tuples into Delta partition columns.

    Delta Lake only supports identity partitioning here, so transforms such as
    ``day`` or ``bucket`` must be rejected explicitly.

    Args:
        partition_spec: Partition specification, either as column names or
            (column, transform) tuples.

    Returns:
        list[str] | None: List of partition column names, or None if no partitioning.

    Raises:
        PhloConfigError: If invalid partition spec format or unsupported transforms.

    Example:
        cols = _partition_columns_from_spec([("date", "identity")])
        # Returns: ["date"]

    """
    if not partition_spec:
        return None

    partition_columns: list[str] = []
    for entry in partition_spec:
        if isinstance(entry, str):
            partition_columns.append(entry)
            continue

        if not isinstance(entry, (tuple, list)) or len(entry) != 2:
            raise PhloConfigError(
                message="Delta partition_spec entries must be column names or (column, transform) pairs",
                suggestions=[
                    "Use partition_spec=[('column', 'identity')] for Delta tables",
                    "Or omit partition_spec entirely for unpartitioned Delta tables",
                ],
            )

        source_name, transform_name = entry
        if not isinstance(source_name, str) or not isinstance(transform_name, str):
            raise PhloConfigError(
                message="Delta partition_spec entries must contain string column and transform names",
                suggestions=[
                    "Use partition_spec=[('column', 'identity')] for Delta tables",
                ],
            )
        if transform_name != "identity":
            raise PhloConfigError(
                message=f"Delta table_store only supports identity partition transforms, got {transform_name!r}",
                suggestions=[
                    "Use partition_spec=[('column', 'identity')] with Delta",
                    "Use phlo-iceberg for transform-based partitioning like day/month/bucket",
                ],
            )
        partition_columns.append(source_name)

    return partition_columns


@dataclass
class DeltaResource:
    """Resource wrapper for Delta Lake table storage.

    This class provides the primary interface for Delta Lake table operations
    within the Phlo framework, implementing the table store protocol.

    Attributes:
        None: This dataclass has no fields, only methods.

    Example:
        resource = DeltaResource()
        table = resource.ensure_table("raw.events", schema)
        stats = resource.append_parquet("raw.events", "/data/file.parquet")

    """

    @property
    def support(self) -> TableStoreSupport:
        """Return Delta table-store support metadata."""
        return TableStoreSupport(
            supports_refs=False,
            partition_transforms=frozenset({"identity"}),
            supports_snapshots=True,
            supports_compaction=True,
            supports_vacuum=True,
        )

    def table_uri(self, table_name: str) -> str:
        """Construct the full S3 path for a Delta table.

        Args:
            table_name: Fully qualified table name (namespace.table).

        Returns:
            str: S3 URI for the Delta table.

        Example:
            uri = resource.table_uri("raw.events")
            # Returns: "s3://lake/warehouse/delta/raw/events"

        """
        from phlo_delta.tables import _resolve_table_uri

        return _resolve_table_uri(table_name)

    def get_table(self, table_name: str) -> Any:
        """Return a DeltaTable handle for the given table.

        Args:
            table_name: Fully qualified table name (namespace.table).

        Returns:
            DeltaTable: Configured Delta table instance.

        Example:
            table = resource.get_table("raw.events")
            version = table.version()

        """
        from deltalake import DeltaTable

        from phlo_delta.tables import _resolve_table_uri

        table_uri = _resolve_table_uri(table_name)
        opts = get_settings().get_storage_options()
        return DeltaTable(table_uri, storage_options=opts)

    def schema_from_validation_schema(
        self, validation_schema: type[DataFrameModel] | type[Any]
    ) -> pa.Schema:
        """Build a PyArrow schema from a validation model for ingestion flows.

        Converts a Pandera DataFrameModel to a PyArrow schema suitable for
        Delta Lake table creation.

        Args:
            validation_schema: Pandera DataFrameModel subclass defining the schema.

        Returns:
            pa.Schema: PyArrow schema equivalent to the validation model.

        Example:
            from my_schemas import EventSchema
            schema = resource.schema_from_validation_schema(EventSchema)

        """
        from phlo_delta.schema_conversion import pandera_to_delta

        return pandera_to_delta(validation_schema)

    def ensure_table(
        self,
        table_name: str,
        schema: pa.Schema,
        partition_spec: Sequence[tuple[str, str] | str] | None = None,
        override_ref: str | None = None,
    ) -> Any:
        """Ensure a table exists and return its handle.

        Creates the table if it does not exist, or returns the existing table.

        Args:
            table_name: Fully qualified table name (namespace.table).
            schema: PyArrow table schema.
            partition_spec: Optional shared partition specification.
            override_ref: Optional branch override for interface compatibility.

        Returns:
            DeltaTable: Existing or newly created Delta table.

        Raises:
            PhloConfigError: If an unsupported override_ref is provided.

        Example:
            table = resource.ensure_table(
                "raw.events",
                schema,
                partition_spec=[("date", "identity")]
            )

        """
        _resolve_delta_ref(override_ref)
        return ensure_table(
            table_name=table_name,
            schema=schema,
            partition_columns=_partition_columns_from_spec(partition_spec),
        )

    def append_parquet(
        self,
        table_name: str,
        data_path: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Append parquet data into a Delta table.

        Reads parquet data from the specified path and appends it to the table.

        Args:
            table_name: Fully qualified table name (namespace.table).
            data_path: Path to parquet input data.
            override_ref: Optional branch override for interface compatibility.

        Returns:
            dict[str, int]: Write statistics from the append operation,
                including rows_inserted and rows_deleted.

        Raises:
            PhloConfigError: If an unsupported override_ref is provided.
            Exception: If the append operation fails.

        Example:
            result = resource.append_parquet("raw.events", "/data/events.parquet")
            print(f"Inserted {result['rows_inserted']} rows")

        """
        _resolve_delta_ref(override_ref)
        logger.info(
            "delta_resource_append_requested",
            table_name=table_name,
            source=data_path,
        )
        try:
            result = append_to_table(table_name=table_name, data_path=data_path)
        except Exception as exc:
            logger.error(
                "delta_resource_append_failed",
                table_name=table_name,
                source=data_path,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "delta_resource_append_completed",
            table_name=table_name,
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
        """Merge parquet data into a Delta table using a unique key.

        Performs an upsert operation: updates existing rows matching the unique key
        and inserts new rows.

        Args:
            table_name: Fully qualified table name (namespace.table).
            data_path: Path to parquet input data.
            unique_key: Column used to match existing rows.
            override_ref: Optional branch override for interface compatibility.

        Returns:
            dict[str, int]: Write statistics from the merge operation,
                including rows_inserted, rows_updated, and rows_deleted.

        Raises:
            PhloConfigError: If an unsupported override_ref is provided.
            Exception: If the merge operation fails.

        Example:
            result = resource.merge_parquet(
                "raw.events", "/data/events.parquet", unique_key="event_id"
            )

        """
        _resolve_delta_ref(override_ref)
        logger.info(
            "delta_resource_merge_requested",
            table_name=table_name,
            source=data_path,
            unique_key=unique_key,
        )
        try:
            result = merge_to_table(
                table_name=table_name,
                data_path=data_path,
                unique_key=unique_key,
            )
        except Exception as exc:
            logger.error(
                "delta_resource_merge_failed",
                table_name=table_name,
                source=data_path,
                unique_key=unique_key,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "delta_resource_merge_completed",
            table_name=table_name,
            source=data_path,
            unique_key=unique_key,
            rows_inserted=result.get("rows_inserted", 0),
            rows_deleted=result.get("rows_deleted", 0),
        )
        return result

    def overwrite_parquet(
        self,
        *,
        table_name: str,
        data_path: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Overwrite a Delta table with staged parquet data.

        Replaces all existing data in the table with the new parquet data.

        Args:
            table_name: Fully qualified table name (namespace.table).
            data_path: Path to parquet input data.
            override_ref: Optional branch override for interface compatibility.

        Returns:
            dict[str, int]: Write statistics from the overwrite operation.

        Raises:
            PhloConfigError: If an unsupported override_ref is provided.
            Exception: If the overwrite operation fails.

        Example:
            result = resource.overwrite_parquet(
                table_name="raw.events",
                data_path="/data/events.parquet"
            )

        """
        _resolve_delta_ref(override_ref)
        logger.info(
            "delta_resource_overwrite_requested",
            table_name=table_name,
            source=data_path,
        )
        try:
            result = overwrite_table(table_name=table_name, data_path=data_path)
        except Exception as exc:
            logger.error(
                "delta_resource_overwrite_failed",
                table_name=table_name,
                source=data_path,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "delta_resource_overwrite_completed",
            table_name=table_name,
            source=data_path,
            rows_inserted=result.get("rows_inserted", 0),
            rows_deleted=result.get("rows_deleted", 0),
        )
        return result

    def delete_rows(
        self,
        *,
        table_name: str,
        predicate: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Delete rows matching a predicate expression.

        Removes rows from the table that match the specified SQL predicate.

        Args:
            table_name: Fully qualified table name (namespace.table).
            predicate: Filter expression (e.g. ``"status = 'inactive'"``).
            override_ref: Optional branch override for interface compatibility.

        Returns:
            dict[str, int]: Delete statistics (rows_deleted is -1 as Delta
                does not return a count from predicate deletes).

        Raises:
            PhloConfigError: If an unsupported override_ref is provided.
            Exception: If the delete operation fails.

        Example:
            result = resource.delete_rows(
                table_name="raw.events",
                predicate="created_at < '2024-01-01'"
            )

        """
        _resolve_delta_ref(override_ref)
        logger.info(
            "delta_resource_delete_rows_requested",
            table_name=table_name,
            predicate=predicate,
        )
        try:
            result = delete_rows_from_table(table_name=table_name, predicate=predicate)
        except Exception as exc:
            logger.error(
                "delta_resource_delete_rows_failed",
                table_name=table_name,
                predicate=predicate,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "delta_resource_delete_rows_completed",
            table_name=table_name,
            predicate=predicate,
        )
        return result

    def compact(self, *, table_name: str) -> dict[str, object]:
        """Compact small files in a table using Delta OPTIMIZE.

        Runs the Delta OPTIMIZE command to coalesce small files into larger ones,
        improving query performance.

        Args:
            table_name: Fully qualified table name (namespace.table).

        Returns:
            dict[str, object]: Compaction results from the optimize operation.

        Example:
            result = resource.compact(table_name="raw.events")
            print(f"Compaction metrics: {result['compaction']}")

        """
        from phlo_delta.tables import _resolve_table_uri

        table_uri = _resolve_table_uri(table_name)
        opts = get_settings().get_storage_options()
        delta_table_cls = _load_delta_table()

        logger.info("delta_resource_compact_requested", table_name=table_name)
        dt = delta_table_cls(table_uri, storage_options=opts)
        result = dt.optimize.compact()
        logger.info("delta_resource_compact_completed", table_name=table_name)
        return {"compaction": result}

    def list_snapshots(self, *, table_name: str, limit: int = 10) -> list[dict]:
        """List recent table versions (Delta equivalent of snapshots).

        Retrieves the version history of the table, showing all changes over time.

        Args:
            table_name: Fully qualified table name (namespace.table).
            limit: Maximum number of versions to return (default: 10).

        Returns:
            list[dict]: Version metadata dicts, most recent first.
                Each dict contains version, timestamp, operation, and parameters.

        Example:
            versions = resource.list_snapshots(table_name="raw.events", limit=5)
            for v in versions:
                print(f"Version {v['version']}: {v['operation']}")

        """
        return list_table_versions(table_name=table_name, limit=limit)

    def rollback_to_snapshot(self, *, table_name: str, snapshot_id: int | str) -> dict:
        """Roll back a table to a previous version.

        Restores the table to a specific historical version using Delta's
        time travel capabilities.

        Args:
            table_name: Fully qualified table name (namespace.table).
            snapshot_id: Target version number to restore to.

        Returns:
            dict: Contains ``rolled_back_to`` version number.

        Raises:
            Exception: If the rollback operation fails.

        Example:
            result = resource.rollback_to_snapshot(
                table_name="raw.events",
                snapshot_id=42
            )
            print(f"Rolled back to version {result['rolled_back_to']}")

        """
        logger.info(
            "delta_resource_rollback_requested",
            table_name=table_name,
            version=snapshot_id,
        )
        try:
            result = rollback_table_to_version(table_name=table_name, version=int(snapshot_id))
        except Exception as exc:
            logger.error(
                "delta_resource_rollback_failed",
                table_name=table_name,
                version=snapshot_id,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "delta_resource_rollback_completed",
            table_name=table_name,
            version=snapshot_id,
        )
        return result

    def vacuum(self, *, table_name: str, retain_hours: int = 168) -> dict:
        """Remove old files via Delta vacuum.

        Deletes old data files that are no longer needed, based on the retention
        period. Default retention is 7 days (168 hours).

        Args:
            table_name: Fully qualified table name (namespace.table).
            retain_hours: Retention period in hours (default 168 = 7 days).

        Returns:
            dict: Vacuum results including files_removed count and removed_files list.

        Raises:
            Exception: If the vacuum operation fails.

        Example:
            result = resource.vacuum(table_name="raw.events", retain_hours=72)
            print(f"Removed {result['files_removed']} files")

        """
        logger.info(
            "delta_resource_vacuum_requested",
            table_name=table_name,
            retain_hours=retain_hours,
        )
        result = remove_orphan_files(table_name=table_name, retain_hours=retain_hours)
        logger.info(
            "delta_resource_vacuum_completed",
            table_name=table_name,
            files_removed=result["files_removed"],
        )
        return result
