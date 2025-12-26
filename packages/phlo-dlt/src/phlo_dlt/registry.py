from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pandera.pandas import DataFrameModel
from phlo.config import config


@dataclass(frozen=True)
class TableConfig:
    table_name: str
    iceberg_schema: Any
    validation_schema: type[DataFrameModel] | None
    unique_key: str
    group_name: str
    partition_spec: list[tuple[str, str]] | None = None

    @property
    def full_table_name(self) -> str:
        return f"{config.iceberg_default_namespace}.{self.table_name}"
