from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pandera.pandas import DataFrameModel

from phlo_dlt.settings import get_settings


@dataclass(frozen=True)
class TableConfig:
    """Configuration describing a registered ingestion table.

    Attributes:
        table_name: Physical target table name.
        table_schema: Optional explicit table-store schema object.
        validation_schema: Optional Pandera schema used for validation.
        unique_key: Column used as unique key for merge semantics.
        group_name: Dagster group name for generated assets.
        partition_spec: Optional table-store partition transform specification.
    """

    table_name: str
    table_schema: Any | None
    validation_schema: type[DataFrameModel] | None
    unique_key: str
    group_name: str
    partition_spec: list[tuple[str, str]] | None = None

    @property
    def full_table_name(self) -> str:
        """Return fully qualified table name with default namespace.

        Returns:
            Namespace-prefixed table name.
        """
        return f"{get_settings().dlt_default_namespace}.{self.table_name}"
