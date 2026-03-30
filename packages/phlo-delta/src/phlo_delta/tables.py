"""Delta Lake table management utilities for creating, modifying, and querying tables.

This module provides standalone functions for Delta table operations using the
deltalake library. It handles table lifecycle operations (create, read, update),
data ingestion from parquet files, maintenance operations (vacuum, optimize),
and version management (time travel, rollback).

All functions operate on fully qualified table names in the format
"namespace.table" and use S3-compatible storage backends.

Example:
    from phlo_delta.tables import ensure_table, append_to_table, get_table_stats
    import pyarrow as pa

    schema = pa.schema([("id", pa.string()), ("value", pa.int64())])
    table = ensure_table("raw.events", schema)

    stats = get_table_stats("raw.events")
    print(f"Table has {stats['file_count']} files")

    result = append_to_table("raw.events", "/data/events.parquet")
    print(f"Inserted {result['rows_inserted']} rows")

"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, cast

import pyarrow as pa
import pyarrow.parquet as pq

from phlo.logging import get_logger
from phlo_delta.settings import get_settings

logger = get_logger(__name__)

DeltaTable = Any
# Type alias for DeltaTable from deltalake package (lazy-loaded).


def _load_deltalake() -> tuple[type[Any], Any]:
    """Load optional deltalake runtime symbols on demand.

    Lazily imports the DeltaTable class and write_deltalake function
    from the deltalake package to avoid import-time dependencies.

    Returns:
        tuple[type[Any], Any]: Tuple containing (DeltaTable class, write_deltalake function).

    Example:
        DeltaTable, write_deltalake = _load_deltalake()
        dt = DeltaTable(table_uri, storage_options=opts)

    """
    deltalake = cast(Any, importlib.import_module("deltalake"))
    return deltalake.DeltaTable, deltalake.write_deltalake


def _resolve_table_uri(table_name: str) -> str:
    """Build a full S3 URI for a Delta table from namespace.table format.

    Constructs the complete S3 path by combining the configured warehouse
    path with the namespace and table name.

    Args:
        table_name: Fully qualified table name (namespace.table).

    Returns:
        str: S3 URI for the Delta table.

    Raises:
        ValueError: If table_name is not in namespace.table format.

    Example:
        uri = _resolve_table_uri("raw.events")
        # Returns: "s3://lake/warehouse/delta/raw/events"

    """
    parts = table_name.split(".")
    if len(parts) != 2:
        raise ValueError(f"Table name must be namespace.table, got: {table_name}")
    namespace, table = parts
    settings = get_settings()
    return f"{settings.delta_warehouse_path}/{namespace}/{table}"


def _default_storage_options(
    storage_options: dict[str, str] | None = None,
) -> dict[str, str]:
    """Return storage options, falling back to settings if not provided.

    Uses provided storage options or retrieves defaults from DeltaSettings.

    Args:
        storage_options: Optional S3 storage options override.

    Returns:
        dict[str, str]: Storage options dictionary with AWS credentials,
            endpoint URL, and other S3 configuration.

    Example:
        opts = _default_storage_options()  # Uses settings
        opts = _default_storage_options({"AWS_REGION": "eu-west-1"})  # Override

    """
    if storage_options is not None:
        return storage_options
    return get_settings().get_storage_options()


def _read_parquet(data_path: str | Path) -> pa.Table:
    """Read parquet data from a file or directory.

    Loads parquet data into a PyArrow Table, supporting both single files
    and directories containing multiple parquet files.

    Args:
        data_path: Path to parquet file or directory.

    Returns:
        pa.Table: PyArrow table containing the parquet data.

    Raises:
        Exception: If reading the parquet data fails.

    Example:
        table = _read_parquet("/data/events.parquet")
        table = _read_parquet("/data/events/")  # Directory of parquet files

    """
    data_path = Path(data_path) if isinstance(data_path, str) else data_path
    if data_path.is_dir():
        return pq.ParquetDataset(str(data_path)).read()
    return pq.read_table(str(data_path))


def ensure_table(
    table_name: str,
    schema: pa.Schema,
    partition_columns: list[str] | None = None,
    storage_options: dict[str, str] | None = None,
) -> DeltaTable:
    """Ensure a Delta table exists, creating it if necessary.

    Checks if the table exists and returns it, or creates a new empty
    table with the specified schema if it does not exist.

    Args:
        table_name: Fully qualified table name (namespace.table).
        schema: PyArrow schema for the table.
        partition_columns: Optional columns to partition by.
        storage_options: S3 storage options override.

    Returns:
        DeltaTable: Existing or newly created Delta table.

    Raises:
        Exception: If table creation fails.

    Example:
        schema = pa.schema([("id", pa.string()), ("value", pa.int64())])
        table = ensure_table("raw.events", schema, partition_columns=["date"])

    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)
    delta_table_cls, write_deltalake = _load_deltalake()

    try:
        dt = delta_table_cls(table_uri, storage_options=opts)
        logger.info(
            "delta_table_loaded",
            table_name=table_name,
            table_uri=table_uri,
        )
        return dt
    except Exception:
        pass

    logger.info(
        "delta_table_creating",
        table_name=table_name,
        table_uri=table_uri,
    )

    empty_table = pa.table(
        {field.name: pa.array([], type=field.type) for field in schema},
        schema=schema,
    )
    write_deltalake(
        table_uri,
        empty_table,
        mode="error",
        partition_by=partition_columns,
        storage_options=opts,
    )

    dt = delta_table_cls(table_uri, storage_options=opts)
    logger.info(
        "delta_table_created",
        table_name=table_name,
        table_uri=table_uri,
    )
    return dt


def append_to_table(
    table_name: str,
    data_path: str | Path,
    storage_options: dict[str, str] | None = None,
) -> dict[str, int]:
    """Append parquet data to a Delta table.

    Reads parquet data from the specified path and appends it to the
    existing table. Creates the table if it does not exist.

    Args:
        table_name: Fully qualified table name (namespace.table).
        data_path: Path to parquet input data (file or directory).
        storage_options: S3 storage options override.

    Returns:
        dict[str, int]: Write statistics from the append operation,
            including rows_inserted (rows_deleted is always 0 for append).

    Raises:
        Exception: If reading parquet or writing to Delta fails.

    Example:
        result = append_to_table("raw.events", "/data/new_events.parquet")
        print(f"Inserted {result['rows_inserted']} rows")

    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)
    _delta_table_cls, write_deltalake = _load_deltalake()
    source_path = str(data_path)
    source_row_count = 0
    rows_inserted = 0

    logger.info(
        "delta_table_append_started",
        table_name=table_name,
        source=source_path,
    )

    try:
        arrow_table = _read_parquet(data_path)
        source_row_count = len(arrow_table)

        write_deltalake(
            table_uri,
            arrow_table,
            mode="append",
            storage_options=opts,
        )
        rows_inserted = source_row_count
    except Exception as exc:
        logger.error(
            "delta_table_append_failed",
            table_name=table_name,
            source=source_path,
            source_row_count=source_row_count,
            rows_inserted=rows_inserted,
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise

    result = {"rows_inserted": rows_inserted, "rows_deleted": 0}
    logger.info(
        "delta_table_append_succeeded",
        table_name=table_name,
        source=source_path,
        source_row_count=source_row_count,
        rows_inserted=result["rows_inserted"],
    )
    return result


def merge_to_table(
    table_name: str,
    data_path: str | Path,
    unique_key: str,
    storage_options: dict[str, str] | None = None,
) -> dict[str, int]:
    """Merge (upsert) parquet data into a Delta table with deduplication.

    Performs a merge operation that updates existing rows matching the
    unique key and inserts new rows. This implements an upsert pattern.

    Args:
        table_name: Fully qualified table name (namespace.table).
        data_path: Path to parquet input data.
        unique_key: Column used to match existing rows (must exist in data).
        storage_options: S3 storage options override.

    Returns:
        dict[str, int]: Write statistics from the merge operation:
            - rows_inserted: Number of new rows added
            - rows_updated: Number of existing rows modified
            - rows_deleted: Number of rows deleted (usually 0)

    Raises:
        ValueError: If the unique_key column is not found in the data.
        Exception: If the merge operation fails.

    Example:
        result = merge_to_table(
            "raw.events",
            "/data/events.parquet",
            unique_key="event_id"
        )
        print(f"Inserted: {result['rows_inserted']}, Updated: {result['rows_updated']}")

    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)
    source_path = str(data_path)
    source_row_count = 0

    logger.info(
        "delta_table_merge_started",
        table_name=table_name,
        source=source_path,
        unique_key=unique_key,
    )
    delta_table_cls, _write_deltalake = _load_deltalake()

    try:
        arrow_table = _read_parquet(data_path)
        source_row_count = len(arrow_table)

        if unique_key not in arrow_table.schema.names:
            raise ValueError(
                f"Unique key '{unique_key}' not found in data. "
                f"Available columns: {arrow_table.schema.names}"
            )

        dt = delta_table_cls(table_uri, storage_options=opts)
        merge_result = (
            dt.merge(
                source=arrow_table,
                predicate=f"target.{unique_key} = source.{unique_key}",
                source_alias="source",
                target_alias="target",
            )
            .when_matched_update_all()
            .when_not_matched_insert_all()
            .execute()
        )

        rows_updated = merge_result.get("num_target_rows_updated", 0)
        rows_inserted = merge_result.get("num_target_rows_inserted", 0)
        rows_deleted = merge_result.get("num_target_rows_deleted", 0)
    except Exception as exc:
        logger.error(
            "delta_table_merge_failed",
            table_name=table_name,
            source=source_path,
            source_row_count=source_row_count,
            unique_key=unique_key,
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise

    result = {
        "rows_inserted": rows_inserted,
        "rows_updated": rows_updated,
        "rows_deleted": rows_deleted,
    }
    logger.info(
        "delta_table_merge_succeeded",
        table_name=table_name,
        source=source_path,
        source_row_count=source_row_count,
        unique_key=unique_key,
        rows_inserted=result["rows_inserted"],
        rows_updated=result["rows_updated"],
        rows_deleted=result["rows_deleted"],
    )
    return result


def overwrite_table(
    table_name: str,
    data_path: str | Path,
    storage_options: dict[str, str] | None = None,
) -> dict[str, int]:
    """Overwrite a Delta table with parquet data.

    Replaces all existing data in the table with the new parquet data.
    The old data is logically replaced but remains accessible via time travel.

    Args:
        table_name: Fully qualified table name (namespace.table).
        data_path: Path to parquet input data.
        storage_options: S3 storage options override.

    Returns:
        dict[str, int]: Write statistics from the overwrite operation,
            including rows_inserted (rows_deleted is always 0 for overwrite).

    Raises:
        Exception: If reading parquet or writing to Delta fails.

    Example:
        result = overwrite_table("raw.events", "/data/full_refresh.parquet")
        print(f"Overwrote with {result['rows_inserted']} rows")

    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)
    _delta_table_cls, write_deltalake = _load_deltalake()
    source_path = str(data_path)
    source_row_count = 0
    rows_inserted = 0

    logger.info(
        "delta_table_overwrite_started",
        table_name=table_name,
        source=source_path,
    )

    try:
        arrow_table = _read_parquet(data_path)
        source_row_count = len(arrow_table)

        write_deltalake(
            table_uri,
            arrow_table,
            mode="overwrite",
            storage_options=opts,
        )
        rows_inserted = source_row_count
    except Exception as exc:
        logger.error(
            "delta_table_overwrite_failed",
            table_name=table_name,
            source=source_path,
            source_row_count=source_row_count,
            rows_inserted=rows_inserted,
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise

    result = {"rows_inserted": rows_inserted, "rows_deleted": 0}
    logger.info(
        "delta_table_overwrite_succeeded",
        table_name=table_name,
        source=source_path,
        source_row_count=source_row_count,
        rows_inserted=result["rows_inserted"],
    )
    return result


def delete_rows_from_table(
    table_name: str,
    predicate: str,
    storage_options: dict[str, str] | None = None,
) -> dict[str, int]:
    """Delete rows matching a predicate expression from a Delta table.

    Removes rows that match the specified SQL predicate condition.
    This operation is atomic and creates a new table version.

    Args:
        table_name: Fully qualified table name (namespace.table).
        predicate: SQL filter expression (e.g. ``"status = 'inactive'"``).
        storage_options: S3 storage options override.

    Returns:
        dict[str, int]: Delete statistics. rows_deleted is always -1
            because Delta does not return a count from predicate deletes.

    Raises:
        Exception: If the delete operation fails.

    Example:
        result = delete_rows_from_table(
            "raw.events",
            predicate="created_at < '2024-01-01'"
        )

    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)

    logger.info(
        "delta_table_delete_started",
        table_name=table_name,
        predicate=predicate,
    )
    delta_table_cls, _write_deltalake = _load_deltalake()

    try:
        dt = delta_table_cls(table_uri, storage_options=opts)
        dt.delete(predicate)
    except Exception as exc:
        logger.error(
            "delta_table_delete_failed",
            table_name=table_name,
            predicate=predicate,
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise

    result = {"rows_deleted": -1}
    logger.info(
        "delta_table_delete_succeeded",
        table_name=table_name,
        predicate=predicate,
    )
    return result


def expire_snapshots(
    table_name: str,
    **_kwargs: Any,
) -> dict[str, Any]:
    """No-op for Delta Lake — snapshot expiration is handled by vacuum.

    Delta Lake does not support explicit snapshot expiration. Old versions
    are automatically managed by the vacuum operation.

    Args:
        table_name: Fully qualified table name (namespace.table).
        **_kwargs: Ignored compatibility arguments.

    Returns:
        dict: Info dict indicating no-op with explanatory note.

    Example:
        result = expire_snapshots("raw.events")
        print(result["note"])  # "Delta Lake does not support explicit snapshot expiration..."

    """
    logger.info(
        "delta_expire_snapshots_noop",
        table_name=table_name,
    )
    return {
        "deleted_snapshots": 0,
        "note": "Delta Lake does not support explicit snapshot expiration; use vacuum instead.",
    }


def remove_orphan_files(
    table_name: str,
    retain_hours: int = 168,
    storage_options: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Remove old files using Delta vacuum.

    Deletes data files that are no longer referenced by the table and
    are older than the retention period. Default retention is 7 days.

    Args:
        table_name: Fully qualified table name (namespace.table).
        retain_hours: Retention period in hours (default 168 = 7 days).
        storage_options: S3 storage options override.

    Returns:
        dict: Vacuum results including:
            - files_removed: Count of files deleted
            - removed_files: List of removed file paths (up to 100)

    Raises:
        Exception: If the vacuum operation fails.

    Example:
        result = remove_orphan_files("raw.events", retain_hours=72)
        print(f"Removed {result['files_removed']} old files")

    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)

    logger.info(
        "delta_vacuum_started",
        table_name=table_name,
        retain_hours=retain_hours,
    )
    delta_table_cls, _write_deltalake = _load_deltalake()

    try:
        dt = delta_table_cls(table_uri, storage_options=opts)
        removed = dt.vacuum(retention_hours=retain_hours, enforce_retention_duration=False)
    except Exception as exc:
        logger.error(
            "delta_vacuum_failed",
            table_name=table_name,
            retain_hours=retain_hours,
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise

    logger.info(
        "delta_vacuum_succeeded",
        table_name=table_name,
        files_removed=len(removed),
    )
    return {
        "files_removed": len(removed),
        "removed_files": removed[:100],
    }


def get_table_stats(
    table_name: str,
    storage_options: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Get statistics about a Delta table.

    Retrieves metadata and statistics about the table including file count,
    total size, version, and partition information.

    Args:
        table_name: Fully qualified table name (namespace.table).
        storage_options: S3 storage options override.

    Returns:
        dict: Table statistics including:
            - table_name: Name of the table
            - version: Current table version
            - file_count: Number of data files
            - total_size_bytes: Total size in bytes
            - total_size_mb: Total size in megabytes
            - table_uri: Full S3 URI of the table
            - description: Table description metadata
            - partition_columns: List of partition columns

    Raises:
        Exception: If the table cannot be accessed.

    Example:
        stats = get_table_stats("raw.events")
        print(f"Table v{stats['version']} has {stats['file_count']} files")

    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)
    delta_table_cls, _write_deltalake = _load_deltalake()

    dt = delta_table_cls(table_uri, storage_options=opts)
    dt_runtime = dt
    files = dt_runtime.files()
    metadata = dt.metadata()
    version = dt.version()

    total_size_bytes = sum(dt_runtime.get_add_actions().to_pydict().get("size", []))

    return {
        "table_name": table_name,
        "version": version,
        "file_count": len(files),
        "total_size_bytes": total_size_bytes,
        "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
        "table_uri": table_uri,
        "description": metadata.description,
        "partition_columns": metadata.partition_columns,
    }


def list_table_versions(
    table_name: str,
    limit: int = 10,
    storage_options: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """List recent versions of a Delta table.

    Retrieves the version history showing all table modifications over time.
    This enables time travel and audit capabilities.

    Args:
        table_name: Fully qualified table name (namespace.table).
        limit: Maximum number of versions to return (default: 10).
        storage_options: S3 storage options override.

    Returns:
        list[dict]: Version history dicts, most recent first. Each dict contains:
            - version: Version number
            - timestamp: ISO timestamp of the operation
            - operation: Type of operation (e.g., "WRITE", "MERGE")
            - operation_parameters: Dict of operation-specific parameters

    Raises:
        Exception: If the table cannot be accessed.

    Example:
        versions = list_table_versions("raw.events", limit=5)
        for v in versions:
            print(f"v{v['version']}: {v['operation']} at {v['timestamp']}")

    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)
    delta_table_cls, _write_deltalake = _load_deltalake()

    dt = delta_table_cls(table_uri, storage_options=opts)
    history = dt.history(limit=limit)

    results: list[dict[str, Any]] = []
    for entry in history:
        results.append(
            {
                "version": entry.get("version"),
                "timestamp": entry.get("timestamp"),
                "operation": entry.get("operation"),
                "operation_parameters": entry.get("operationParameters"),
            }
        )
    return results


def rollback_table_to_version(
    table_name: str,
    version: int,
    storage_options: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Roll back a Delta table to a previous version.

    Restores the table to a specific historical version using Delta's
    time travel restore capability. This creates a new version that
    matches the specified historical version.

    Args:
        table_name: Fully qualified table name (namespace.table).
        version: Target version number to restore to.
        storage_options: S3 storage options override.

    Returns:
        dict: Contains rolled_back_to version number.

    Raises:
        Exception: If the rollback operation fails.

    Example:
        result = rollback_table_to_version("raw.events", version=42)
        print(f"Rolled back to version {result['rolled_back_to']}")

    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)

    logger.info(
        "delta_table_rollback_started",
        table_name=table_name,
        version=version,
    )
    delta_table_cls, _write_deltalake = _load_deltalake()

    try:
        dt = delta_table_cls(table_uri, storage_options=opts)
        dt.restore(version)
    except Exception as exc:
        logger.error(
            "delta_table_rollback_failed",
            table_name=table_name,
            version=version,
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise

    logger.info(
        "delta_table_rollback_succeeded",
        table_name=table_name,
        version=version,
    )
    return {"rolled_back_to": version}
