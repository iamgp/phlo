from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from pyiceberg.schema import Schema
from pandera.pandas import DataFrameModel

from cascade.config import config


@dataclass(frozen=True)
class TableConfig:
    """
    Configuration for a single ingestion table.

    Used internally by the @cascade_ingestion decorator to package
    all table metadata together.

    Attributes:
        table_name: Iceberg table name (without namespace)
        iceberg_schema: PyIceberg Schema for table creation
        validation_schema: Pandera DataFrameModel for data validation (optional)
        unique_key: Column name for idempotent merge/deduplication
        group_name: Dagster asset group name
        partition_spec: Iceberg partition spec (optional)
    """

    table_name: str
    iceberg_schema: Schema
    validation_schema: type[DataFrameModel] | None
    unique_key: str
    group_name: str
    partition_spec: Sequence[tuple[str, str]] | None = None

    @property
    def full_table_name(self) -> str:
        """Get fully qualified table name (namespace.table_name)."""
        return f"{config.iceberg_default_namespace}.{self.table_name}"
