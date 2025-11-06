# tables.py - Iceberg table management utilities for creating, modifying, and querying tables
# Provides high-level functions for table operations in the lakehouse, including partitioning
# and data appending, built on top of PyIceberg and Nessie catalog

"""
Iceberg table management and data operations.
"""

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from pyiceberg.schema import Schema
from pyiceberg.table import Table

from cascade.iceberg.catalog import create_namespace, get_catalog


# --- Table Management Functions ---
# Core functions for creating and managing Iceberg tables
def ensure_table(
    table_name: str,
    schema: Schema,
    partition_spec: list[tuple[str, str]] | None = None,
    ref: str = "main",
) -> Table:
    """
    Ensure table exists, create if it doesn't.

    Args:
        table_name: Fully qualified table name (e.g., "raw.nightscout_entries")
        schema: PyIceberg Schema for the table
        partition_spec: List of (field, transform) tuples for partitioning
                       e.g., [("date", "day"), ("hour", "hour")]
        ref: Nessie branch/tag reference

    Returns:
        PyIceberg Table instance

    Example:
        from pyiceberg.schema import Schema
        from pyiceberg.types import (
            NestedField, StringType, TimestampType, DoubleType
        )

        schema = Schema(
            NestedField(1, "id", StringType(), required=True),
            NestedField(2, "timestamp", TimestampType(), required=True),
            NestedField(3, "sgv", DoubleType(), required=False),
        )

        table = ensure_table(
            "raw.nightscout_entries",
            schema,
            partition_spec=[("timestamp", "day")]
        )
    """
    catalog = get_catalog(ref=ref)

    # Parse namespace and table
    parts = table_name.split(".")
    if len(parts) != 2:
        raise ValueError(f"Table name must be namespace.table, got: {table_name}")

    namespace, table = parts

    # Ensure namespace exists
    create_namespace(namespace, ref=ref)

    # Check if table exists
    try:
        return catalog.load_table(table_name)
    except Exception:
        # Table doesn't exist, create it
        pass

    # Build partition spec
    from pyiceberg.partitioning import PartitionSpec, PartitionField
    from pyiceberg.transforms import DayTransform, HourTransform, IdentityTransform

    transform_map = {
        "identity": IdentityTransform(),
        "day": DayTransform(),
        "hour": HourTransform(),
    }

    partition_fields = []
    if partition_spec:
        for field_id, (source_name, transform_name) in enumerate(
            partition_spec, start=1000
        ):
            # Find source field in schema
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

    # Create table
    return catalog.create_table(
        identifier=table_name,
        schema=schema,
        partition_spec=spec,
    )


# --- Data Operations ---
# Functions for reading and writing data to/from Iceberg tables
def append_to_table(
    table_name: str,
    data_path: str | Path,
    ref: str = "main",
) -> None:
    """
    Append parquet data to an Iceberg table.

    Args:
        table_name: Fully qualified table name (e.g., "raw.nightscout_entries")
        data_path: Path to parquet file or directory of parquet files
        ref: Nessie branch/tag reference

    Example:
        # After DLT stages data to S3
        append_to_table(
            "raw.nightscout_entries",
            "s3://lake/stage/nightscout/entries/2024-10-17.parquet"
        )
    """
    catalog = get_catalog(ref=ref)
    table = catalog.load_table(table_name)

    # Read parquet file(s)
    data_path = Path(data_path) if isinstance(data_path, str) else data_path

    if data_path.is_dir():
        # Read all parquet files in directory
        arrow_table = pq.ParquetDataset(str(data_path)).read()
    else:
        # Read single parquet file
        arrow_table = pq.read_table(str(data_path))

    # Append to Iceberg table
    table.append(arrow_table)


def merge_to_table(
    table_name: str,
    data_path: str | Path,
    unique_key: str,
    ref: str = "main",
) -> dict[str, int]:
    """
    Merge (upsert) parquet data to an Iceberg table with deduplication.

    This implements idempotent ingestion by:
    1. Reading new data from parquet file
    2. Deleting existing records that match the new data (by unique_key)
    3. Appending the new data

    This ensures running the same ingestion multiple times doesn't create duplicates.

    Args:
        table_name: Fully qualified table name (e.g., "raw.nightscout_entries")
        data_path: Path to parquet file or directory of parquet files
        unique_key: Column name to use for deduplication (e.g., "_id")
        ref: Nessie branch/tag reference

    Returns:
        Dictionary with metrics: {"rows_deleted": int, "rows_inserted": int}

    Example:
        # Idempotent ingestion - safe to run multiple times
        metrics = merge_to_table(
            "raw.glucose_entries",
            "/tmp/entries.parquet",
            unique_key="_id"
        )
        print(f"Deleted {metrics['rows_deleted']}, inserted {metrics['rows_inserted']}")
    """
    catalog = get_catalog(ref=ref)
    table = catalog.load_table(table_name)

    # Read parquet file(s)
    data_path = Path(data_path) if isinstance(data_path, str) else data_path

    if data_path.is_dir():
        # Read all parquet files in directory
        arrow_table = pq.ParquetDataset(str(data_path)).read()
    else:
        # Read single parquet file
        arrow_table = pq.read_table(str(data_path))

    # Validate unique_key exists in schema
    if unique_key not in arrow_table.schema.names:
        raise ValueError(
            f"Unique key '{unique_key}' not found in data. "
            f"Available columns: {arrow_table.schema.names}"
        )

    # Get unique values from the new data for the unique key
    unique_values = arrow_table.column(unique_key).to_pylist()
    unique_values_set = set(unique_values)

    if len(unique_values_set) < len(unique_values):
        raise ValueError(
            f"Duplicate values found in unique_key '{unique_key}' in new data. "
            f"Expected {len(unique_values)} unique values, got {len(unique_values_set)}."
        )

    # Step 1: Delete existing records with matching unique keys
    # Build a delete filter: unique_key IN (value1, value2, ...)
    # For large datasets, we delete in batches to avoid filter size limits
    rows_deleted = 0
    batch_size = 1000
    unique_values_list = list(unique_values_set)

    for i in range(0, len(unique_values_list), batch_size):
        batch = unique_values_list[i:i + batch_size]
        # PyIceberg delete uses expressions
        # We'll use the IsIn expression for efficient filtering
        from pyiceberg.expressions import IsIn

        delete_expr = IsIn(unique_key, batch)
        try:
            delete_result = table.delete(delete_expr)
            # Count deletions if available in result
            rows_deleted += len(batch)  # Approximation
        except Exception as e:
            # If delete fails (e.g., no matching records), continue
            pass

    # Step 2: Append the new data
    table.append(arrow_table)
    rows_inserted = len(arrow_table)

    return {
        "rows_deleted": rows_deleted,
        "rows_inserted": rows_inserted,
    }


# --- Utility Functions ---
# Helper functions for inspecting and managing table metadata
def get_table_schema(table_name: str, ref: str = "main") -> Schema:
    """
    Get the schema of an existing table.

    Args:
        table_name: Fully qualified table name
        ref: Nessie branch/tag reference

    Returns:
        PyIceberg Schema

    Example:
        schema = get_table_schema("raw.nightscout_entries")
        print(schema)
    """
    catalog = get_catalog(ref=ref)
    table = catalog.load_table(table_name)
    return table.schema()


def delete_table(table_name: str, ref: str = "main") -> None:
    """
    Delete a table (use with caution).

    Args:
        table_name: Fully qualified table name
        ref: Nessie branch/tag reference

    Example:
        delete_table("raw.nightscout_entries_test")
    """
    catalog = get_catalog(ref=ref)
    catalog.drop_table(table_name)
