"""Tests for executor-level strict validation semantics."""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest
from pandera.pandas import DataFrameModel
from pandera.typing import Series  # type: ignore[possibly-missing-import]

from phlo.logging import get_logger
from phlo_dlt.executor import DltIngester
from phlo_dlt.registry import TableConfig


class StrictExecutorSchema(DataFrameModel):
    """Schema used to verify executor-level strict validation behavior."""

    name: Series[str]
    value: Series[int]


def test_strict_validation_blocks_visible_write(monkeypatch, tmp_path) -> None:
    invalid_path = tmp_path / "invalid.parquet"
    pd.DataFrame([{"name": "test", "value": "not_an_int"}]).to_parquet(invalid_path)
    merge_called = False

    monkeypatch.setattr(
        "phlo_dlt.executor.setup_dlt_pipeline",
        lambda **_kwargs: (SimpleNamespace(), tmp_path),
    )
    monkeypatch.setattr(
        "phlo_dlt.executor.stage_to_parquet",
        lambda **_kwargs: ([invalid_path], 0.01),
    )

    def _merge_to_table_store(**_kwargs):
        nonlocal merge_called
        merge_called = True
        return {"rows_inserted": 1, "rows_deleted": 0}

    monkeypatch.setattr("phlo_dlt.executor.merge_to_table_store", _merge_to_table_store)

    ingester = DltIngester(
        context=None,
        logger=get_logger("test_dlt_executor_strict_validation"),
        table_config=TableConfig(
            table_name="entries",
            table_schema=None,
            validation_schema=StrictExecutorSchema,
            unique_key="name",
            group_name="raw",
        ),
        table_store_resource=SimpleNamespace(),
        dlt_source_func=lambda partition_date: object(),
        validation_schema=StrictExecutorSchema,
        validate=True,
        strict_validation=True,
    )

    with pytest.raises(RuntimeError, match="Pandera contract validation failed"):
        ingester.run_ingestion(partition_key="2026-03-05")

    assert merge_called is False


def test_non_strict_validation_allows_write_and_records_evaluation(monkeypatch, tmp_path) -> None:
    invalid_path = tmp_path / "invalid.parquet"
    pd.DataFrame([{"name": "test", "value": "not_an_int"}]).to_parquet(invalid_path)

    monkeypatch.setattr(
        "phlo_dlt.executor.setup_dlt_pipeline",
        lambda **_kwargs: (SimpleNamespace(), tmp_path),
    )
    monkeypatch.setattr(
        "phlo_dlt.executor.stage_to_parquet",
        lambda **_kwargs: ([invalid_path], 0.01),
    )
    monkeypatch.setattr(
        "phlo_dlt.executor.merge_to_table_store",
        lambda **_kwargs: {"rows_inserted": 1, "rows_deleted": 0},
    )

    ingester = DltIngester(
        context=None,
        logger=get_logger("test_dlt_executor_non_strict_validation"),
        table_config=TableConfig(
            table_name="entries",
            table_schema=None,
            validation_schema=StrictExecutorSchema,
            unique_key="name",
            group_name="raw",
        ),
        table_store_resource=SimpleNamespace(),
        dlt_source_func=lambda partition_date: object(),
        validation_schema=StrictExecutorSchema,
        validate=True,
        strict_validation=False,
    )

    result = ingester.run_ingestion(partition_key="2026-03-05")

    assert result.status == "success"
    assert result.metadata["pandera_evaluation"]["passed"] is False
