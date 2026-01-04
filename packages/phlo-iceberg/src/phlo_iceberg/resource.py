from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from phlo.config import config
from pyiceberg.catalog import Catalog
from pyiceberg.schema import Schema
from pyiceberg.table import Table

from phlo_iceberg.catalog import get_catalog
from phlo_iceberg.tables import append_to_table, ensure_table, merge_to_table


@dataclass
class IcebergResource:
    """Resource wrapper for the Nessie-backed Iceberg catalog."""

    ref: str = config.iceberg_nessie_ref

    def get_catalog(self, override_ref: str | None = None) -> Catalog:
        branch = override_ref or self.ref
        return get_catalog(ref=branch)

    def ensure_table(
        self,
        table_name: str,
        schema: Schema,
        partition_spec: Sequence[tuple[str, str]] | None = None,
        override_ref: str | None = None,
    ) -> Table:
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
        branch = override_ref or self.ref
        return append_to_table(table_name=table_name, data_path=data_path, ref=branch)

    def merge_parquet(
        self,
        table_name: str,
        data_path: str,
        unique_key: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        branch = override_ref or self.ref
        return merge_to_table(
            table_name=table_name,
            data_path=data_path,
            unique_key=unique_key,
            ref=branch,
        )
