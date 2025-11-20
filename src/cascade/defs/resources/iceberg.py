# iceberg.py - Dagster resource for Iceberg table operations with Nessie catalog integration
# Provides a configurable resource that wraps PyIceberg catalog operations
# for table management and data appending in the lakehouse pipeline

from __future__ import annotations

from collections.abc import Sequence

from dagster import ConfigurableResource
from pyiceberg.catalog import Catalog
from pyiceberg.schema import Schema
from pyiceberg.table import Table

from cascade.config import config
from cascade.iceberg import append_to_table, ensure_table, get_catalog, merge_to_table


# --- Resource Classes ---
# Dagster resources for external service integration
class IcebergResource(ConfigurableResource):
    """
    Dagster resource wrapping access to the Nessie-backed Iceberg catalog.

    Provides convenience helpers for the common table operations the pipeline
    performs (ensuring tables exist and appending new parquet data).

    The default Nessie ref can be configured via ICEBERG_NESSIE_REF env var,
    or overridden per-resource instance.
    """

    ref: str = config.iceberg_nessie_ref  # Default from config (typically "main" for production)

    def get_catalog(self, override_ref: str | None = None) -> Catalog:
        """
        Return the PyIceberg catalog for the specified branch.

        Args:
            override_ref: Override default ref for this operation
        """
        branch = override_ref or self.ref
        return get_catalog(ref=branch)

    def ensure_table(
        self,
        table_name: str,
        schema: Schema,
        partition_spec: Sequence[tuple[str, str]] | None = None,
        override_ref: str | None = None,
    ) -> Table:
        """
        Ensure the requested table exists on the specified Nessie ref and return it.

        Args:
            table_name: Fully qualified table name (namespace.table)
            schema: Iceberg schema
            partition_spec: Optional partitioning
            override_ref: Override default branch
        """
        branch = override_ref or self.ref
        return ensure_table(
            table_name=table_name,
            schema=schema,
            partition_spec=list(partition_spec) if partition_spec else None,
            ref=branch,
        )

    def append_parquet(self, table_name: str, data_path: str, override_ref: str | None = None) -> None:
        """
        Append a parquet file or directory to the Iceberg table.

        Args:
            table_name: Fully qualified table name
            data_path: Path to parquet file or directory
            override_ref: Override default branch
        """
        branch = override_ref or self.ref
        append_to_table(table_name=table_name, data_path=data_path, ref=branch)

    def merge_parquet(
        self, table_name: str, data_path: str, unique_key: str, override_ref: str | None = None
    ) -> dict[str, int]:
        """
        Merge (upsert) a parquet file or directory to the Iceberg table with deduplication.

        This implements idempotent ingestion - safe to run multiple times without
        creating duplicate records.

        Args:
            table_name: Fully qualified table name (e.g., "raw.glucose_entries")
            data_path: Path to parquet file or directory
            unique_key: Column name to use for deduplication (e.g., "_id")
            override_ref: Override default branch

        Returns:
            Dictionary with metrics: {"rows_deleted": int, "rows_inserted": int}
        """
        branch = override_ref or self.ref
        return merge_to_table(
            table_name=table_name,
            data_path=data_path,
            unique_key=unique_key,
            ref=branch,
        )
