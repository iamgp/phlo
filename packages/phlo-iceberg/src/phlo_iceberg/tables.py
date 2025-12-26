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
