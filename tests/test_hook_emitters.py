"""Tests for hook emitters."""

from __future__ import annotations

from typing import Any

import pytest

from phlo.hooks.emitters import IngestionEventContext, IngestionEventEmitter
from phlo.logging import bind_context, clear_context

pytestmark = pytest.mark.core_regression


def test_ingestion_emitter_merges_bound_correlation_context() -> None:
    class RecordingBus:
        def __init__(self) -> None:
            self.events: list[Any] = []

        def emit(self, event: Any) -> None:
            self.events.append(event)

    bus = RecordingBus()
    emitter = IngestionEventEmitter(
        IngestionEventContext(
            asset_key="silver.orders",
            table_name="orders",
            group_name="sales",
            run_id="run-123",
            partition_key="2026-03-08",
        ),
        hook_bus=bus,
    )

    bind_context(trace_id="abc123", span_id="def456", job_name="daily_orders")
    try:
        emitter.emit_end(status="success", metrics={"rows_loaded": 10})
    finally:
        clear_context()

    event = bus.events[0]
    assert event.correlation.run_id == "run-123"
    assert event.correlation.asset_key == "silver.orders"
    assert event.correlation.partition_key == "2026-03-08"
    assert event.correlation.job_name == "daily_orders"
    assert event.correlation.trace_id == "abc123"
    assert event.correlation.span_id == "def456"
