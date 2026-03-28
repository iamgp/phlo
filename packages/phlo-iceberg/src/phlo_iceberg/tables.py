"""Iceberg table management utilities for creating, modifying, and querying tables.

This module provides high-level operations for Iceberg table management including
creating tables, appending/merging data, snapshot management, and cleanup operations.

All table names must be fully qualified as ``namespace.table``.

Example:
    Basic table operations::

        from phlo_iceberg.tables import ensure_table, append_to_table, merge_to_table
        from pyiceberg.schema import Schema
        from pyiceberg.types import NestedField, StringType, LongType

        # Create or get existing table
        schema = Schema(
            NestedField(1, "id", LongType(), required=True),
            NestedField(2, "name", StringType(), required=False),
        )
        table = ensure_table("raw.users", schema=schema)

        # Append data
        result = append_to_table("raw.users", data_path="/data/users.parquet")
        print(f"Inserted {result['rows_inserted']} rows")

        # Merge (upsert) data by unique key
        result = merge_to_table(
            "raw.users",
            data_path="/data/updates.parquet",
            unique_key="id"
        )
        print(f"Updated {result['rows_deleted']} rows, inserted {result['rows_inserted']} rows")

Ported from ``phlo`` core as a capability plugin.

"""

from __future__ import annotations

import warnings
from pathlib import Path

import pyarrow.parquet as pq
from pyiceberg.exceptions import TableAlreadyExistsError
from pyiceberg.schema import Schema
from pyiceberg.table import Table

from phlo.logging import get_logger
from phlo_iceberg.catalog import create_namespace, get_catalog

# Suppress expected pyiceberg warning on first run (no rows to delete during merge)
warnings.filterwarnings(
    "ignore",
    message="Delete operation did not match any records",
    category=UserWarning,
)

logger = get_logger(__name__)


def _align_arrow_table_to_target_schema(arrow_table, target_schema, *, table_name: str):
    """Align an Arrow table to an Iceberg target schema.

    Missing nullable target columns are backfilled with nulls. Missing required
    columns fail explicitly so callers get a useful schema error.

    Args:
        arrow_table: PyArrow Table to align.
        target_schema: Target Iceberg schema as PyArrow schema.
        table_name: Name of the target table for error messages.

    Returns:
        PyArrow Table aligned to target schema with columns in correct order.

    Raises:
        ValueError: If a required column is missing from the source data.

    Example:
        Align table before appending::

            aligned = _align_arrow_table_to_target_schema(
                arrow_table, target_schema, table_name="raw.users"
            )

    """
    import pyarrow as pa

    arrow_column_names = set(arrow_table.schema.names)
    for field in target_schema:
        if field.name in arrow_column_names:
            continue
        if not field.nullable:
            raise ValueError(
                f"Required target column '{field.name}' is missing from source data for {table_name}"
            )
        arrow_table = arrow_table.append_column(
            field.name,
            pa.nulls(len(arrow_table), type=field.type),
        )

    return arrow_table.select(target_schema.names)


def ensure_table(
    table_name: str,
    schema: Schema,
    partition_spec: list[tuple[str, str]] | None = None,
    ref: str = "main",
) -> Table:
    """Ensure an Iceberg table exists, creating it if necessary.

    Checks if the table exists in the catalog. If not, creates it with the
    specified schema and optional partitioning. The namespace is created
    automatically if it doesn't exist.

    Args:
        table_name: Fully qualified table name in ``namespace.table`` format.
        schema: Iceberg schema defining table structure.
        partition_spec: Optional partitioning specification as list of
            ``(column_name, transform)`` tuples. Supported transforms:
            ``identity``, ``day``, ``hour``, ``month``, ``year``.
        ref: Nessie branch/tag reference (default: ``main``).

    Returns:
        Table: Existing or newly created Iceberg table handle.

    Raises:
        ValueError: If table name format is invalid or partition spec is malformed.
        TableAlreadyExistsError: Re-raises and returns existing table on race condition.

    Example:
        Create a partitioned table::

            from pyiceberg.schema import Schema
            from pyiceberg.types import NestedField, LongType, StringType, TimestamptzType

            schema = Schema(
                NestedField(1, "id", LongType(), required=True),
                NestedField(2, "event_time", TimestamptzType(), required=True),
                NestedField(3, "name", StringType(), required=False),
            )

            table = ensure_table(
                "raw.events",
                schema=schema,
                partition_spec=[("event_time", "day")],
                ref="main"
            )

    """
    catalog = get_catalog(ref=ref)

    parts = table_name.split(".")
    if len(parts) != 2:
        raise ValueError(f"Table name must be namespace.table, got: {table_name}")

    namespace, _ = parts

    create_namespace(namespace, ref=ref)

    try:
        return catalog.load_table(table_name)
    except Exception:
        pass

    from pyiceberg.partitioning import PartitionField, PartitionSpec
    from pyiceberg.transforms import (
        DayTransform,
        HourTransform,
        IdentityTransform,
        MonthTransform,
        YearTransform,
    )

    transform_map = {
        "identity": IdentityTransform(),
        "day": DayTransform(),
        "hour": HourTransform(),
        "month": MonthTransform(),
        "year": YearTransform(),
    }

    partition_fields = []
    if partition_spec:
        for field_id, (source_name, transform_name) in enumerate(partition_spec, start=1000):
            source_field = None
            for field in schema.fields:
                if field.name == source_name:
                    source_field = field
                    break

            if not source_field:
                raise ValueError(f"Partition source field not found: {source_name}")

            transform = transform_map.get(transform_name)
            if not transform:
                raise ValueError(f"Unknown transform: {transform_name}")

            partition_fields.append(
                PartitionField(
                    source_id=source_field.field_id,
                    field_id=field_id,
                    transform=transform,
                    name=f"{source_name}_{transform_name}",
                )
            )

    spec = PartitionSpec(*partition_fields) if partition_fields else PartitionSpec()

    try:
        return catalog.create_table(
            identifier=table_name,
            schema=schema,
            partition_spec=spec,
        )
    except TableAlreadyExistsError:
        logger.info("iceberg_table_exists_during_create", table_name=table_name, ref=ref)
        return catalog.load_table(table_name)


def append_to_table(
    table_name: str,
    data_path: str | Path,
    ref: str = "main",
) -> dict[str, int]:
    """Append Parquet data to an Iceberg table.

    Reads data from a Parquet file or directory and appends it to the specified
    table. Automatically aligns the data schema to match the target table,
    handling missing columns by backfilling nulls for nullable fields.

    Args:
        table_name: Fully qualified table name in ``namespace.table`` format.
        data_path: Path to Parquet file or directory containing data files.
        ref: Nessie branch/tag reference (default: ``main``).

    Returns:
        dict: Operation statistics containing:
            - ``rows_inserted``: Number of rows successfully appended.
            - ``rows_deleted``: Always 0 for append operations.

    Raises:
        ValueError: If required columns are missing from source data.
        Exception: Re-raises any PyIceberg or Parquet read errors.

    Example:
        Append single Parquet file::

            result = append_to_table(
                table_name="raw.events",
                data_path="/data/events_2024-01-01.parquet"
            )
            print(f"Appended {result['rows_inserted']} rows")

        Append directory of Parquet files::

            result = append_to_table(
                table_name="raw.events",
                data_path="/data/daily_batches/",
                ref="main"
            )

    """
    source_path = str(data_path)
    source_row_count = 0
    rows_inserted = 0

    logger.info(
        "iceberg_table_append_started",
        table_name=table_name,
        ref=ref,
        source=source_path,
        source_row_count=source_row_count,
    )

    try:
        catalog = get_catalog(ref=ref)
        table = catalog.load_table(table_name)

        data_path = Path(data_path) if isinstance(data_path, str) else data_path

        if data_path.is_dir():
            arrow_table = pq.ParquetDataset(str(data_path)).read()
        else:
            arrow_table = pq.read_table(str(data_path))

        source_row_count = len(arrow_table)

        iceberg_column_names = {field.name for field in table.schema().fields}
        arrow_column_names = set(arrow_table.schema.names)
        new_columns = arrow_column_names - iceberg_column_names

        if new_columns:
            logger.warning(
                "arrow_columns_not_in_iceberg_schema",
                new_column_count=len(new_columns),
                new_columns=sorted(new_columns),
                table_name=table_name,
            )
            existing_columns = [c for c in arrow_table.schema.names if c in iceberg_column_names]
            arrow_table = arrow_table.select(existing_columns)

        import pyarrow as pa
        from pyiceberg.io.pyarrow import schema_to_pyarrow

        target_schema = schema_to_pyarrow(table.schema())

        arrow_table = _align_arrow_table_to_target_schema(
            arrow_table, target_schema, table_name=table_name
        )

        try:
            arrow_table = arrow_table.cast(target_schema)
        except (pa.ArrowInvalid, pa.ArrowTypeError, ValueError) as e:
            logger.warning(
                "arrow_cast_to_target_schema_failed", table_name=table_name, error=str(e)
            )

        table.append(arrow_table)
        rows_inserted = len(arrow_table)
        result = {"rows_inserted": rows_inserted, "rows_deleted": 0}
    except Exception as exc:
        logger.error(
            "iceberg_table_append_failed",
            table_name=table_name,
            ref=ref,
            source=source_path,
            source_row_count=source_row_count,
            rows_inserted=rows_inserted,
            rows_deleted=0,
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise

    logger.info(
        "iceberg_table_append_succeeded",
        table_name=table_name,
        ref=ref,
        source=source_path,
        source_row_count=source_row_count,
        rows_inserted=result["rows_inserted"],
        rows_deleted=result["rows_deleted"],
    )

    return result


def merge_to_table(
    table_name: str,
    data_path: str | Path,
    unique_key: str,
    ref: str = "main",
) -> dict[str, int]:
    """Merge (upsert) Parquet data into an Iceberg table with deduplication.

    Performs a merge operation that deletes existing rows matching the unique key
    before inserting new data. This effectively implements an upsert pattern.
    Duplicate values within the source data are detected and logged as warnings.

    The merge operation:
        1. Reads source Parquet data
        2. Identifies unique key values in source data
        3. Deletes existing rows with matching keys (in batches of 1000)
        4. Appends source data to table

    Args:
        table_name: Fully qualified table name in ``namespace.table`` format.
        data_path: Path to Parquet file or directory containing data files.
        unique_key: Column name used to identify matching rows for deletion.
        ref: Nessie branch/tag reference (default: ``main``).

    Returns:
        dict: Operation statistics containing:
            - ``rows_deleted``: Approximate count of rows deleted (may include
              non-existent keys).
            - ``rows_inserted``: Number of rows successfully inserted.

    Raises:
        ValueError: If the unique_key column is not found in source data.
        Exception: Re-raises any PyIceberg or Parquet read errors.

    Example:
        Upsert user data by ID::

            result = merge_to_table(
                table_name="raw.users",
                data_path="/data/user_updates.parquet",
                unique_key="user_id"
            )
            print(f"Deleted ~{result['rows_deleted']} existing rows")
            print(f"Inserted {result['rows_inserted']} new rows")

    Warning:
        The ``rows_deleted`` count is an approximation because Iceberg's
        delete operation doesn't return the actual number of rows deleted.
        It represents the number of unique keys processed, not necessarily
        the count of existing rows removed.

    """
    source_path = str(data_path)
    source_row_count = 0
    rows_deleted = 0
    rows_inserted = 0

    logger.info(
        "iceberg_table_merge_started",
        table_name=table_name,
        ref=ref,
        source=source_path,
        source_row_count=source_row_count,
        unique_key=unique_key,
    )

    try:
        catalog = get_catalog(ref=ref)
        table = catalog.load_table(table_name)

        data_path = Path(data_path) if isinstance(data_path, str) else data_path

        if data_path.is_dir():
            arrow_table = pq.ParquetDataset(str(data_path)).read()
        else:
            arrow_table = pq.read_table(str(data_path))

        source_row_count = len(arrow_table)

        if unique_key not in arrow_table.schema.names:
            raise ValueError(
                f"Unique key '{unique_key}' not found in data. "
                f"Available columns: {arrow_table.schema.names}"
            )

        unique_values = arrow_table.column(unique_key).to_pylist()
        unique_values_set = set(unique_values)

        if len(unique_values_set) < len(unique_values):
            duplicates_count = len(unique_values) - len(unique_values_set)
            logger.warning(
                "source_duplicates_detected_after_deduplication",
                duplicates_count=duplicates_count,
                unique_key=unique_key,
                table_name=table_name,
            )

        batch_size = 1000
        unique_values_list = list(unique_values_set)

        for i in range(0, len(unique_values_list), batch_size):
            batch = unique_values_list[i : i + batch_size]
            from pyiceberg.expressions import In

            delete_expr = In(unique_key, batch)
            try:
                table.delete(delete_expr)
                rows_deleted += len(batch)  # Approximation
            except Exception:
                pass

        iceberg_column_names = {field.name for field in table.schema().fields}
        arrow_column_names = set(arrow_table.schema.names)
        new_columns = arrow_column_names - iceberg_column_names

        if new_columns:
            logger.warning(
                "arrow_columns_not_in_iceberg_schema",
                new_column_count=len(new_columns),
                new_columns=sorted(new_columns),
                table_name=table_name,
            )
            existing_columns = [c for c in arrow_table.schema.names if c in iceberg_column_names]
            arrow_table = arrow_table.select(existing_columns)

        import pyarrow as pa
        from pyiceberg.io.pyarrow import schema_to_pyarrow

        target_schema = schema_to_pyarrow(table.schema())

        arrow_table = _align_arrow_table_to_target_schema(
            arrow_table, target_schema, table_name=table_name
        )

        try:
            arrow_table = arrow_table.cast(target_schema)
        except (pa.ArrowInvalid, pa.ArrowTypeError, ValueError) as e:
            logger.warning(
                "arrow_cast_to_target_schema_failed", table_name=table_name, error=str(e)
            )

        table.append(arrow_table)
        rows_inserted = len(arrow_table)

    except Exception as exc:
        logger.error(
            "iceberg_table_merge_failed",
            table_name=table_name,
            ref=ref,
            source=source_path,
            source_row_count=source_row_count,
            unique_key=unique_key,
            rows_deleted=rows_deleted,
            rows_inserted=rows_inserted,
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise

    result = {"rows_deleted": rows_deleted, "rows_inserted": rows_inserted}
    logger.info(
        "iceberg_table_merge_succeeded",
        table_name=table_name,
        ref=ref,
        source=source_path,
        source_row_count=source_row_count,
        unique_key=unique_key,
        rows_deleted=result["rows_deleted"],
        rows_inserted=result["rows_inserted"],
    )

    return result


def overwrite_table(
    table_name: str,
    data_path: str | Path,
    ref: str = "main",
) -> dict[str, int]:
    """Overwrite an Iceberg table with Parquet data.

    Replaces all existing data in the table with the contents of the source
    Parquet file(s). Creates a new snapshot. The previous data remains
    accessible via snapshot history until snapshots are expired.

    Args:
        table_name: Fully qualified table name in ``namespace.table`` format.
        data_path: Path to Parquet file or directory containing replacement data.
        ref: Nessie branch/tag reference (default: ``main``).

    Returns:
        dict: Operation statistics containing:
            - ``rows_inserted``: Number of rows in replacement data.
            - ``rows_deleted``: Always 0 (full replacement, not row-level delete).

    Raises:
        ValueError: If required columns are missing from source data.
        Exception: Re-raises any PyIceberg or Parquet read errors.

    Example:
        Full table replacement::

            result = overwrite_table(
                table_name="raw.daily_summary",
                data_path="/data/regenerated_summary.parquet"
            )
            print(f"Table now contains {result['rows_inserted']} rows")

    See Also:
        :func:`merge_to_table`: For partial updates without full replacement.

    """
    source_path = str(data_path)
    source_row_count = 0
    rows_inserted = 0

    logger.info(
        "iceberg_table_overwrite_started",
        table_name=table_name,
        ref=ref,
        source=source_path,
    )

    try:
        catalog = get_catalog(ref=ref)
        table = catalog.load_table(table_name)

        data_path = Path(data_path) if isinstance(data_path, str) else data_path

        if data_path.is_dir():
            arrow_table = pq.ParquetDataset(str(data_path)).read()
        else:
            arrow_table = pq.read_table(str(data_path))

        source_row_count = len(arrow_table)

        iceberg_column_names = {field.name for field in table.schema().fields}
        arrow_column_names = set(arrow_table.schema.names)
        new_columns = arrow_column_names - iceberg_column_names

        if new_columns:
            logger.warning(
                "arrow_columns_not_in_iceberg_schema",
                new_column_count=len(new_columns),
                new_columns=sorted(new_columns),
                table_name=table_name,
            )
            existing_columns = [c for c in arrow_table.schema.names if c in iceberg_column_names]
            arrow_table = arrow_table.select(existing_columns)

        import pyarrow as pa
        from pyiceberg.io.pyarrow import schema_to_pyarrow

        target_schema = schema_to_pyarrow(table.schema())

        arrow_table = _align_arrow_table_to_target_schema(
            arrow_table, target_schema, table_name=table_name
        )

        try:
            arrow_table = arrow_table.cast(target_schema)
        except (pa.ArrowInvalid, pa.ArrowTypeError, ValueError) as e:
            logger.warning(
                "arrow_cast_to_target_schema_failed", table_name=table_name, error=str(e)
            )

        table.overwrite(arrow_table)
        rows_inserted = len(arrow_table)
        result = {"rows_inserted": rows_inserted, "rows_deleted": 0}
    except Exception as exc:
        logger.error(
            "iceberg_table_overwrite_failed",
            table_name=table_name,
            ref=ref,
            source=source_path,
            source_row_count=source_row_count,
            rows_inserted=rows_inserted,
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise

    logger.info(
        "iceberg_table_overwrite_succeeded",
        table_name=table_name,
        ref=ref,
        source=source_path,
        source_row_count=source_row_count,
        rows_inserted=result["rows_inserted"],
        rows_deleted=result["rows_deleted"],
    )

    return result


def delete_rows_from_table(
    table_name: str,
    predicate: str,
    ref: str = "main",
) -> dict[str, int]:
    """Delete rows matching a predicate expression from an Iceberg table.

    Uses Iceberg's delete operation with a filter predicate. The predicate
    should be a valid Iceberg SQL expression string.

    Args:
        table_name: Fully qualified table name in ``namespace.table`` format.
        predicate: Filter expression string (e.g., ``"status = 'inactive'"``,
            ``"created_at < '2024-01-01'"``).
        ref: Nessie branch/tag reference (default: ``main``).

    Returns:
        dict: Operation statistics containing:
            - ``rows_deleted``: Always -1 (PyIceberg doesn't return delete count).

    Raises:
        Exception: Re-raises any PyIceberg errors during delete.

    Example:
        Delete old records::

            result = delete_rows_from_table(
                table_name="raw.events",
                predicate="event_time < '2024-01-01T00:00:00Z'"
            )

        Delete by status::

            delete_rows_from_table(
                table_name="raw.users",
                predicate="account_status = 'deleted'"
            )

    Note:
        PyIceberg does not return the number of rows actually deleted.
        The ``rows_deleted`` value will always be -1.

    """
    logger.info(
        "iceberg_table_delete_started",
        table_name=table_name,
        ref=ref,
        predicate=predicate,
    )

    try:
        catalog = get_catalog(ref=ref)
        table = catalog.load_table(table_name)
        table.delete(delete_filter=predicate)
    except Exception as exc:
        logger.error(
            "iceberg_table_delete_failed",
            table_name=table_name,
            ref=ref,
            predicate=predicate,
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise

    result = {"rows_deleted": -1}
    logger.info(
        "iceberg_table_delete_succeeded",
        table_name=table_name,
        ref=ref,
        predicate=predicate,
    )

    return result


def list_table_snapshots(
    table_name: str,
    limit: int = 10,
    ref: str = "main",
) -> list[dict]:
    """List recent snapshots of an Iceberg table.

    Args:
        table_name: Fully qualified table name (namespace.table).
        limit: Maximum number of snapshots to return.
        ref: Nessie branch reference.

    Returns:
        List of snapshot dicts (most recent first), each with snapshot_id,
        timestamp_ms, operation, and summary.

    """
    catalog = get_catalog(ref=ref)
    table = catalog.load_table(table_name)

    snapshots = sorted(table.snapshots(), key=lambda s: s.timestamp_ms, reverse=True)

    results: list[dict] = []
    for snap in snapshots[:limit]:
        results.append(
            {
                "snapshot_id": snap.snapshot_id,
                "timestamp_ms": snap.timestamp_ms,
                "operation": snap.summary.operation.value if snap.summary else None,
                "summary": dict(snap.summary.additional_properties) if snap.summary else {},
            }
        )

    return results


def rollback_table_to_snapshot(
    table_name: str,
    snapshot_id: int,
    ref: str = "main",
) -> dict:
    """Roll back an Iceberg table to a previous snapshot.

    Args:
        table_name: Fully qualified table name (namespace.table).
        snapshot_id: Target snapshot ID.
        ref: Nessie branch reference.

    Returns:
        Dict with rolled_back_to snapshot ID.

    """
    logger.info(
        "iceberg_table_rollback_started",
        table_name=table_name,
        ref=ref,
        snapshot_id=snapshot_id,
    )

    try:
        catalog = get_catalog(ref=ref)
        table = catalog.load_table(table_name)
        table.manage_snapshots().rollback_to(snapshot_id).commit()
    except Exception as exc:
        logger.error(
            "iceberg_table_rollback_failed",
            table_name=table_name,
            ref=ref,
            snapshot_id=snapshot_id,
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise

    logger.info(
        "iceberg_table_rollback_succeeded",
        table_name=table_name,
        ref=ref,
        snapshot_id=snapshot_id,
    )

    return {"rolled_back_to": snapshot_id}


def get_table_schema(table_name: str, ref: str = "main") -> Schema:
    """Get the current schema of an Iceberg table.

    Args:
        table_name: Fully qualified table name in ``namespace.table`` format.
        ref: Nessie branch/tag reference (default: ``main``).

    Returns:
        Schema: The Iceberg schema object for the table.

    Example:
        Inspect table structure::

            schema = get_table_schema("raw.events")
            for field in schema.fields:
                print(f"{field.name}: {field.field_type}")

    """
    catalog = get_catalog(ref=ref)
    table = catalog.load_table(table_name)
    return table.schema()


def delete_table(table_name: str, ref: str = "main") -> None:
    """Permanently delete an Iceberg table from the catalog.

    Warning:
        This operation is irreversible. While the underlying data files
        may persist in storage until cleanup, the table metadata is
        permanently removed from the catalog.

    Args:
        table_name: Fully qualified table name in ``namespace.table`` format.
        ref: Nessie branch/tag reference (default: ``main``).

    Raises:
        Exception: Re-raises any PyIceberg errors during deletion.

    Example:
        Remove table with confirmation::

            delete_table("raw.temp_data", ref="main")
            print("Table deleted from catalog")

    See Also:
        :func:`remove_orphan_files`: To clean up underlying storage files.

    """


def expire_snapshots(
    table_name: str,
    older_than_days: int | None = None,
    retain_last: int = 5,
    ref: str = "main",
    *,
    older_than_hours: int | None = None,
) -> dict[str, int]:
    """Expire old snapshots from an Iceberg table.

    Args:
        table_name: Fully qualified table name (namespace.table)
        older_than_days: Expire snapshots older than this many days (must be positive).
            Mutually exclusive with ``older_than_hours``; defaults to 7 when neither is set.
        retain_last: Always retain at least this many snapshots (must be non-negative)
        ref: Nessie branch reference
        older_than_hours: Expire snapshots older than this many hours (must be positive).

    Returns:
        Dict with deleted_snapshots count

    Raises:
        ValueError: If both ``older_than_days`` and ``older_than_hours`` are set,
            retention <= 0, retain_last < 0, or table_name format invalid.

    """
    from datetime import datetime, timedelta, timezone

    if older_than_days is not None and older_than_hours is not None:
        raise ValueError("Specify older_than_days or older_than_hours, not both")
    if older_than_hours is not None:
        if older_than_hours <= 0:
            raise ValueError(f"older_than_hours must be positive, got {older_than_hours}")
        retention = timedelta(hours=older_than_hours)
    else:
        effective_days = older_than_days if older_than_days is not None else 7
        if effective_days <= 0:
            raise ValueError(f"older_than_days must be positive, got {effective_days}")
        retention = timedelta(days=effective_days)
    if retain_last < 0:
        raise ValueError(f"retain_last must be non-negative, got {retain_last}")
    if "." not in table_name:
        raise ValueError(f"table_name must be namespace.table format, got {table_name}")

    catalog = get_catalog(ref=ref)
    table = catalog.load_table(table_name)

    older_than_ms = int((datetime.now(timezone.utc) - retention).timestamp() * 1000)

    snapshots_before = len(list(table.snapshots()))

    table.manage_snapshots().expire_snapshots_older_than(
        older_than_ms=older_than_ms,
        retain_last=retain_last,
    ).commit()

    table.refresh()
    snapshots_after = len(list(table.snapshots()))
    deleted = snapshots_before - snapshots_after

    logger.info("snapshots_expired", table_name=table_name, deleted_snapshots=deleted)
    return {"deleted_snapshots": deleted}


def remove_orphan_files(
    table_name: str,
    older_than_days: int | None = None,
    dry_run: bool = True,
    ref: str = "main",
    *,
    older_than_hours: int | None = None,
) -> dict[str, int | list[str] | bool]:
    """Remove orphan files not referenced by any snapshot.

    WARNING: When dry_run=False, this operation permanently deletes files from storage.
    There is a race condition risk if new snapshots are being written concurrently.
    Always test with dry_run=True first and ensure no concurrent writes during cleanup.

    Args:
        table_name: Fully qualified table name (namespace.table)
        older_than_days: Only remove files older than this many days (must be positive).
            Mutually exclusive with ``older_than_hours``; defaults to 3 when neither is set.
        dry_run: If True, only list files without deleting
        ref: Nessie branch reference
        older_than_hours: Only remove files older than this many hours (must be positive).

    Returns:
        Dict with orphan_count, orphan_files list, and dry_run flag

    Raises:
        ValueError: If both ``older_than_days`` and ``older_than_hours`` are set,
            retention <= 0, or table_name format invalid.

    """
    from datetime import datetime, timedelta, timezone

    if older_than_days is not None and older_than_hours is not None:
        raise ValueError("Specify older_than_days or older_than_hours, not both")
    if older_than_hours is not None:
        if older_than_hours <= 0:
            raise ValueError(f"older_than_hours must be positive, got {older_than_hours}")
        retention = timedelta(hours=older_than_hours)
    else:
        effective_days = older_than_days if older_than_days is not None else 3
        if effective_days <= 0:
            raise ValueError(f"older_than_days must be positive, got {effective_days}")
        retention = timedelta(days=effective_days)
    if "." not in table_name:
        raise ValueError(f"table_name must be namespace.table format, got {table_name}")

    catalog = get_catalog(ref=ref)
    table = catalog.load_table(table_name)

    older_than_ts = (datetime.now(timezone.utc) - retention).timestamp()

    # Collect all referenced files from all snapshots
    referenced_files: set[str] = set()

    for snapshot in table.snapshots():
        for manifest in snapshot.manifests(table.io):
            referenced_files.add(manifest.manifest_path)
            for entry in manifest.fetch_manifest_entry(table.io):
                referenced_files.add(entry.data_file.file_path)

    # Get table location and list all files
    table_location = table.location()
    io = table.io

    orphan_files: list[str] = []

    try:
        # List files in data directory
        data_location = f"{table_location}/data"
        for file_info in io.list(data_location):
            if file_info.path not in referenced_files:
                # Check if file is old enough
                if hasattr(file_info, "mtime") and file_info.mtime:
                    if file_info.mtime < older_than_ts:
                        orphan_files.append(file_info.path)
                else:
                    orphan_files.append(file_info.path)
    except Exception as e:
        logger.warning("orphan_file_listing_failed", table_location=table_location, error=str(e))

    if dry_run:
        logger.info(
            "orphan_files_found_dry_run",
            table_name=table_name,
            orphan_file_count=len(orphan_files),
        )
    else:
        deleted_count = 0
        for orphan in orphan_files:
            try:
                io.delete(orphan)
                deleted_count += 1
            except Exception as e:
                logger.warning("orphan_file_delete_failed", orphan_file=orphan, error=str(e))
        logger.info(
            "orphan_files_removed",
            table_name=table_name,
            deleted_file_count=deleted_count,
        )

    return {
        "orphan_count": len(orphan_files),
        "orphan_files": orphan_files[:100],  # Limit list size
        "dry_run": dry_run,
    }


def get_table_stats(table_name: str, ref: str = "main") -> dict:
    """Get statistics about an Iceberg table.

    Returns:
        Dict with snapshot_count, file_count, total_size_bytes, etc.

    """
    catalog = get_catalog(ref=ref)
    table = catalog.load_table(table_name)

    snapshots = list(table.snapshots())
    snapshot_count = len(snapshots)

    file_count = 0
    total_size_bytes = 0
    total_records = 0

    current_snapshot = table.current_snapshot()
    if current_snapshot:
        for manifest in current_snapshot.manifests(table.io):
            for entry in manifest.fetch_manifest_entry(table.io):
                file_count += 1
                total_size_bytes += entry.data_file.file_size_in_bytes
                total_records += entry.data_file.record_count

    return {
        "table_name": table_name,
        "snapshot_count": snapshot_count,
        "file_count": file_count,
        "total_size_bytes": total_size_bytes,
        "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
        "total_records": total_records,
        "location": table.location(),
    }
