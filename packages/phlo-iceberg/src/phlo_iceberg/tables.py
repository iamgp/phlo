"""
Iceberg table management utilities for creating, modifying, and querying tables.

Ported from `phlo` core as a capability plugin.
"""

from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
from pyiceberg.schema import Schema
from pyiceberg.table import Table

from phlo_iceberg.catalog import create_namespace, get_catalog


def ensure_table(
    table_name: str,
    schema: Schema,
    partition_spec: list[tuple[str, str]] | None = None,
    ref: str = "main",
) -> Table:
    """Ensure table exists, create if it doesn't."""
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
    from pyiceberg.transforms import DayTransform, HourTransform, IdentityTransform

    transform_map = {
        "identity": IdentityTransform(),
        "day": DayTransform(),
        "hour": HourTransform(),
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

    return catalog.create_table(
        identifier=table_name,
        schema=schema,
        partition_spec=spec,
    )


def append_to_table(
    table_name: str,
    data_path: str | Path,
    ref: str = "main",
) -> dict[str, int]:
    """Append parquet data to an Iceberg table."""
    catalog = get_catalog(ref=ref)
    table = catalog.load_table(table_name)

    data_path = Path(data_path) if isinstance(data_path, str) else data_path

    if data_path.is_dir():
        arrow_table = pq.ParquetDataset(str(data_path)).read()
    else:
        arrow_table = pq.read_table(str(data_path))

    iceberg_column_names = {field.name for field in table.schema().fields}
    arrow_column_names = set(arrow_table.schema.names)
    new_columns = arrow_column_names - iceberg_column_names

    if new_columns:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(
            f"Arrow data has {len(new_columns)} columns not in Iceberg schema: {new_columns}. "
            f"These columns will be dropped. To include them, recreate the table."
        )
        existing_columns = [c for c in arrow_table.schema.names if c in iceberg_column_names]
        arrow_table = arrow_table.select(existing_columns)

    import pyarrow as pa
    from pyiceberg.io.pyarrow import schema_to_pyarrow

    target_schema = schema_to_pyarrow(table.schema())

    arrow_column_names_set = set(arrow_table.schema.names)
    missing_columns = []

    for field in target_schema:
        if field.name not in arrow_column_names_set:
            null_array = pa.nulls(len(arrow_table), type=field.type)
            missing_columns.append((field.name, null_array))

    for col_name, null_array in missing_columns:
        arrow_table = arrow_table.append_column(col_name, null_array)

    target_field_names = target_schema.names
    arrow_table = arrow_table.select(target_field_names)

    try:
        arrow_table = arrow_table.cast(target_schema)
    except (pa.ArrowInvalid, pa.ArrowTypeError, ValueError) as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Could not cast arrow table to target schema: {e}")

    table.append(arrow_table)
    rows_inserted = len(arrow_table)

    return {"rows_inserted": rows_inserted, "rows_deleted": 0}


def merge_to_table(
    table_name: str,
    data_path: str | Path,
    unique_key: str,
    ref: str = "main",
) -> dict[str, int]:
    """
    Merge (upsert) parquet data to an Iceberg table with deduplication.
    """
    catalog = get_catalog(ref=ref)
    table = catalog.load_table(table_name)

    data_path = Path(data_path) if isinstance(data_path, str) else data_path

    if data_path.is_dir():
        arrow_table = pq.ParquetDataset(str(data_path)).read()
    else:
        arrow_table = pq.read_table(str(data_path))

    if unique_key not in arrow_table.schema.names:
        raise ValueError(
            f"Unique key '{unique_key}' not found in data. "
            f"Available columns: {arrow_table.schema.names}"
        )

    unique_values = arrow_table.column(unique_key).to_pylist()
    unique_values_set = set(unique_values)

    if len(unique_values_set) < len(unique_values):
        import logging

        logger = logging.getLogger(__name__)
        duplicates_count = len(unique_values) - len(unique_values_set)
        logger.warning(
            f"{duplicates_count} duplicate values found in unique_key '{unique_key}' "
            f"after source deduplication. This may indicate a configuration issue. "
            f"Consider enabling source deduplication in merge_config."
        )

    rows_deleted = 0
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
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(
            f"Arrow data has {len(new_columns)} columns not in Iceberg schema: {new_columns}. "
            f"These columns will be dropped. To include them, recreate the table."
        )
        existing_columns = [c for c in arrow_table.schema.names if c in iceberg_column_names]
        arrow_table = arrow_table.select(existing_columns)

    import pyarrow as pa
    from pyiceberg.io.pyarrow import schema_to_pyarrow

    target_schema = schema_to_pyarrow(table.schema())

    target_field_names = target_schema.names
    arrow_table = arrow_table.select(target_field_names)

    try:
        arrow_table = arrow_table.cast(target_schema)
    except (pa.ArrowInvalid, pa.ArrowTypeError, ValueError) as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Could not cast arrow table to target schema: {e}")

    table.append(arrow_table)
    rows_inserted = len(arrow_table)

    return {"rows_deleted": rows_deleted, "rows_inserted": rows_inserted}


def get_table_schema(table_name: str, ref: str = "main") -> Schema:
    """Get the schema of an existing table."""
    catalog = get_catalog(ref=ref)
    table = catalog.load_table(table_name)
    return table.schema()


def delete_table(table_name: str, ref: str = "main") -> None:
    """Delete a table (use with caution)."""
    catalog = get_catalog(ref=ref)
    catalog.drop_table(table_name)


def expire_snapshots(
    table_name: str,
    older_than_days: int = 7,
    retain_last: int = 5,
    ref: str = "main",
) -> dict[str, int]:
    """
    Expire old snapshots from an Iceberg table.

    Args:
        table_name: Fully qualified table name (namespace.table)
        older_than_days: Expire snapshots older than this many days
        retain_last: Always retain at least this many snapshots
        ref: Nessie branch reference

    Returns:
        Dict with deleted_snapshots count
    """
    import logging
    from datetime import datetime, timedelta, timezone

    logger = logging.getLogger(__name__)
    catalog = get_catalog(ref=ref)
    table = catalog.load_table(table_name)

    older_than_ms = int(
        (datetime.now(timezone.utc) - timedelta(days=older_than_days)).timestamp() * 1000
    )

    snapshots_before = len(list(table.snapshots()))

    table.manage_snapshots().expire_snapshots_older_than(
        older_than_ms=older_than_ms,
        retain_last=retain_last,
    ).commit()

    table.refresh()
    snapshots_after = len(list(table.snapshots()))
    deleted = snapshots_before - snapshots_after

    logger.info(f"Expired {deleted} snapshots from {table_name}")
    return {"deleted_snapshots": deleted}


def remove_orphan_files(
    table_name: str,
    older_than_days: int = 3,
    dry_run: bool = True,
    ref: str = "main",
) -> dict[str, int | list[str]]:
    """
    Remove orphan files not referenced by any snapshot.

    Args:
        table_name: Fully qualified table name (namespace.table)
        older_than_days: Only remove files older than this many days
        dry_run: If True, only list files without deleting
        ref: Nessie branch reference

    Returns:
        Dict with orphan_files list and count
    """
    import logging
    from datetime import datetime, timedelta, timezone

    logger = logging.getLogger(__name__)
    catalog = get_catalog(ref=ref)
    table = catalog.load_table(table_name)

    older_than_ts = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).timestamp()

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
        logger.warning(f"Could not list files in {table_location}: {e}")

    if dry_run:
        logger.info(f"Found {len(orphan_files)} orphan files in {table_name} (dry run)")
    else:
        deleted_count = 0
        for orphan in orphan_files:
            try:
                io.delete(orphan)
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Could not delete orphan file {orphan}: {e}")
        logger.info(f"Removed {deleted_count} orphan files from {table_name}")

    return {
        "orphan_count": len(orphan_files),
        "orphan_files": orphan_files[:100],  # Limit list size
        "dry_run": dry_run,
    }


def get_table_stats(table_name: str, ref: str = "main") -> dict:
    """
    Get statistics about an Iceberg table.

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
