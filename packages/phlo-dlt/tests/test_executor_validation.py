"""Tests for executor-level strict validation semantics."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pandas as pd
import pytest
from pandera.pandas import DataFrameModel
from pandera.typing import Series  # type: ignore[possibly-missing-import]

from phlo.logging import get_logger
from phlo.hooks.events import IngestionEvent, TelemetryEvent
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
        table_store_resource=cast(Any, SimpleNamespace()),
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
        table_store_resource=cast(Any, SimpleNamespace()),
        dlt_source_func=lambda partition_date: object(),
        validation_schema=StrictExecutorSchema,
        validate=True,
        strict_validation=False,
    )

    result = ingester.run_ingestion(partition_key="2026-03-05")

    assert result.status == "success"
    assert result.metadata["pandera_evaluation"]["passed"] is False


def test_dlt_failure_events_carry_runtime_correlation(monkeypatch, tmp_path) -> None:
    class RecordingBus:
        def __init__(self) -> None:
            self.events: list[object] = []

        def emit(self, event: object) -> None:
            self.events.append(event)

    bus = RecordingBus()
    monkeypatch.setattr("phlo.hooks.emitters.get_hook_bus", lambda: bus)
    monkeypatch.setattr(
        "phlo_dlt.executor.setup_dlt_pipeline",
        lambda **_kwargs: (SimpleNamespace(), tmp_path),
    )
    monkeypatch.setattr(
        "phlo_dlt.executor.stage_to_parquet",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("stage failed")),
    )

    runtime = SimpleNamespace(run_id="run-22", job_name="daily_ingestion")
    ingester = DltIngester(
        context=runtime,
        logger=get_logger("test_dlt_executor_correlation"),
        table_config=TableConfig(
            table_name="entries",
            table_schema=None,
            validation_schema=StrictExecutorSchema,
            unique_key="name",
            group_name="raw",
        ),
        table_store_resource=cast(Any, SimpleNamespace()),
        dlt_source_func=lambda partition_date: object(),
        validation_schema=StrictExecutorSchema,
        validate=False,
    )

    with pytest.raises(RuntimeError, match="stage failed"):
        ingester.run_ingestion(
            partition_key="2026-03-05",
            parameters={"run_id": "run-22", "branch_name": "main"},
        )

    ingestion_events = [event for event in bus.events if isinstance(event, IngestionEvent)]
    telemetry_events = [event for event in bus.events if isinstance(event, TelemetryEvent)]
    assert ingestion_events
    assert telemetry_events
    ingestion = ingestion_events[-1]
    telemetry = telemetry_events[-1]
    assert ingestion.correlation.run_id == "run-22"
    assert ingestion.correlation.job_name == "daily_ingestion"
    assert ingestion.correlation.partition_key == "2026-03-05"
    assert ingestion.correlation.asset_key == "dlt_entries"
    assert telemetry.correlation.run_id == "run-22"
    assert telemetry.correlation.job_name == "daily_ingestion"
    assert telemetry.correlation.partition_key == "2026-03-05"
    assert telemetry.correlation.asset_key == "dlt_entries"
