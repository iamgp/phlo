from __future__ import annotations

from collections.abc import Sequence

from dagster import ConfigurableResource
from pyiceberg.catalog import Catalog
from pyiceberg.schema import Schema
from pyiceberg.table import Table

from cascade.config import config
from cascade.iceberg import append_to_table, ensure_table, get_catalog


class IcebergResource(ConfigurableResource):
    """
    Dagster resource wrapping access to the Nessie-backed Iceberg catalog.

    Provides convenience helpers for the common table operations the pipeline
    performs (ensuring tables exist and appending new parquet data).

    The default Nessie ref can be configured via ICEBERG_NESSIE_REF env var,
    or overridden per-resource instance.
    """

    ref: str = config.iceberg_nessie_ref

    def get_catalog(self) -> Catalog:
        """Return the configured PyIceberg catalog."""
        return get_catalog(ref=self.ref)

    def ensure_table(
        self,
        table_name: str,
        schema: Schema,
        partition_spec: Sequence[tuple[str, str]] | None = None,
    ) -> Table:
        """
        Ensure the requested table exists on the configured Nessie ref and return it.
        """
        return ensure_table(
            table_name=table_name,
            schema=schema,
            partition_spec=list(partition_spec) if partition_spec else None,
            ref=self.ref,
        )

    def append_parquet(self, table_name: str, data_path: str) -> None:
        """Append a parquet file or directory to the Iceberg table."""
        append_to_table(table_name=table_name, data_path=data_path, ref=self.ref)
