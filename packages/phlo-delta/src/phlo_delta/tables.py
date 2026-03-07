"""
Delta Lake table management utilities for creating, modifying, and querying tables.

Provides standalone functions for Delta table operations using the deltalake library.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
from deltalake import DeltaTable, write_deltalake

from phlo.logging import get_logger
from phlo_delta.settings import get_settings

logger = get_logger(__name__)


def _resolve_table_uri(table_name: str) -> str:
    """Build a full S3 URI for a Delta table from namespace.table format.

    Args:
        table_name: Fully qualified table name (namespace.table).

    Returns:
        str: S3 URI for the Delta table.

    Raises:
        ValueError: If table_name is not in namespace.table format.
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
    """Return storage options, falling back to settings if not provided."""
    if storage_options is not None:
        return storage_options
    return get_settings().get_storage_options()


def _read_parquet(data_path: str | Path) -> pa.Table:
    """Read parquet data from a file or directory."""
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

    Args:
        table_name: Fully qualified table name (namespace.table).
        schema: PyArrow schema for the table.
        partition_columns: Optional columns to partition by.
        storage_options: S3 storage options override.

    Returns:
        DeltaTable: Existing or newly created Delta table.
    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)

    try:
        dt = DeltaTable(table_uri, storage_options=opts)
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

    dt = DeltaTable(table_uri, storage_options=opts)
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

    Args:
        table_name: Fully qualified table name (namespace.table).
        data_path: Path to parquet input data.
        storage_options: S3 storage options override.

    Returns:
        dict[str, int]: Write statistics from the append operation.
    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)
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

    Args:
        table_name: Fully qualified table name (namespace.table).
        data_path: Path to parquet input data.
        unique_key: Column used to match existing rows.
        storage_options: S3 storage options override.

    Returns:
        dict[str, int]: Write statistics from the merge operation.
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

    try:
        arrow_table = _read_parquet(data_path)
        source_row_count = len(arrow_table)

        if unique_key not in arrow_table.schema.names:
            raise ValueError(
                f"Unique key '{unique_key}' not found in data. "
                f"Available columns: {arrow_table.schema.names}"
            )

        dt = DeltaTable(table_uri, storage_options=opts)
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

    Args:
        table_name: Fully qualified table name (namespace.table).
        data_path: Path to parquet input data.
        storage_options: S3 storage options override.

    Returns:
        dict[str, int]: Write statistics from the overwrite operation.
    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)
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

    Args:
        table_name: Fully qualified table name (namespace.table).
        predicate: SQL filter expression (e.g. ``"status = 'inactive'"``).
        storage_options: S3 storage options override.

    Returns:
        dict[str, int]: Delete statistics.
    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)

    logger.info(
        "delta_table_delete_started",
        table_name=table_name,
        predicate=predicate,
    )

    try:
        dt = DeltaTable(table_uri, storage_options=opts)
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

    Args:
        table_name: Fully qualified table name (namespace.table).

    Returns:
        dict: Info dict indicating no-op.
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

    Args:
        table_name: Fully qualified table name (namespace.table).
        retain_hours: Retention period in hours (default 168 = 7 days).
        storage_options: S3 storage options override.

    Returns:
        dict: Vacuum results.
    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)

    logger.info(
        "delta_vacuum_started",
        table_name=table_name,
        retain_hours=retain_hours,
    )

    try:
        dt = DeltaTable(table_uri, storage_options=opts)
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

    Args:
        table_name: Fully qualified table name (namespace.table).
        storage_options: S3 storage options override.

    Returns:
        dict: Table statistics including file count, size, and version info.
    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)

    dt = DeltaTable(table_uri, storage_options=opts)
    files = dt.files()
    metadata = dt.metadata()
    version = dt.version()

    total_size_bytes = sum(f.size for f in dt.get_add_actions().to_pydict().get("size", []))

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

    Args:
        table_name: Fully qualified table name (namespace.table).
        limit: Maximum number of versions to return.
        storage_options: S3 storage options override.

    Returns:
        list[dict]: Version history dicts, most recent first.
    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)

    dt = DeltaTable(table_uri, storage_options=opts)
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

    Args:
        table_name: Fully qualified table name (namespace.table).
        version: Target version number.
        storage_options: S3 storage options override.

    Returns:
        dict: Contains rolled_back_to version.
    """
    table_uri = _resolve_table_uri(table_name)
    opts = _default_storage_options(storage_options)

    logger.info(
        "delta_table_rollback_started",
        table_name=table_name,
        version=version,
    )

    try:
        dt = DeltaTable(table_uri, storage_options=opts)
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
