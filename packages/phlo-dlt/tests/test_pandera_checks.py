"""Tests for Pandera parquet contract helpers."""

from __future__ import annotations

import pandas as pd
from pandera.pandas import Field
from pandera.pandas import DataFrameModel
from pandera.typing import Series  # type: ignore[possibly-missing-import]

from phlo_dlt.pandera_checks import (
    evaluate_pandera_contract,
    evaluate_pandera_contract_parquet_files,
)


class MultiFileSchema(DataFrameModel):
    """Schema used to validate combined parquet staging outputs."""

    id: Series[int]
    name: Series[str]


class NullableFieldSchema(DataFrameModel):
    """Schema used to validate widening changes with nullable columns."""

    id: Series[int]
    habitat: Series[str] = Field(nullable=True)


def test_evaluate_pandera_contract_parquet_files_combines_file_set(tmp_path) -> None:
    left_path = tmp_path / "left.parquet"
    right_path = tmp_path / "right.parquet"
    pd.DataFrame([{"id": 1, "name": "alpha"}]).to_parquet(left_path)
    pd.DataFrame([{"id": 2, "name": "beta"}]).to_parquet(right_path)

    evaluation = evaluate_pandera_contract_parquet_files(
        [left_path, right_path],
        schema_class=MultiFileSchema,
    )

    assert evaluation.passed is True
    assert evaluation.total_count == 2
    assert evaluation.failed_count == 0


def test_evaluate_pandera_contract_backfills_missing_nullable_columns() -> None:
    evaluation = evaluate_pandera_contract(
        pd.DataFrame([{"id": 1}]),
        schema_class=NullableFieldSchema,
    )

    assert evaluation.passed is True
    assert evaluation.total_count == 1
    assert evaluation.failed_count == 0
