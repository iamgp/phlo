from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pyiceberg.catalog import Catalog
from pyiceberg.schema import Schema
from pyiceberg.table import Table

from phlo_iceberg.catalog import get_catalog
from phlo_iceberg.settings import get_settings
from phlo_iceberg.tables import append_to_table, ensure_table, merge_to_table


@dataclass
class IcebergResource:
    """Resource wrapper for the Nessie-backed Iceberg catalog."""

    ref: str = field(default_factory=lambda: get_settings().iceberg_nessie_ref)

    def get_catalog(self, override_ref: str | None = None) -> Catalog:
        """Return an Iceberg catalog client for the active branch.

        Args:
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            Catalog: Configured Iceberg catalog instance.
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
        """Ensure a table exists and return its handle.

        Args:
            table_name: Fully qualified table name.
            schema: Iceberg table schema.
            partition_spec: Optional list of ``(field, transform)`` partition rules.
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            Table: Existing or newly created Iceberg table.
        """
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
        """Append parquet data into an Iceberg table.

        Args:
            table_name: Fully qualified table name.
            data_path: Path to parquet input data.
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Write statistics from the append operation.
        """
        branch = override_ref or self.ref
        return append_to_table(table_name=table_name, data_path=data_path, ref=branch)

    def merge_parquet(
        self,
        table_name: str,
        data_path: str,
        unique_key: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Merge parquet data into an Iceberg table using a unique key.

        Args:
            table_name: Fully qualified table name.
            data_path: Path to parquet input data.
            unique_key: Column used to match existing rows.
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Write statistics from the merge operation.
        """
        branch = override_ref or self.ref
        return merge_to_table(
            table_name=table_name,
            data_path=data_path,
            unique_key=unique_key,
            ref=branch,
        )
