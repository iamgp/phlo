from __future__ import annotations

from pathlib import Path

from phlo_api.observatory_api.v2_models import (
    V2Action,
    V2ActionResult,
    V2Health,
    V2Operation,
    V2ResourceRef,
)
from phlo_api.observatory_api.v2_operation_journal import (
    append_operation,
    load_operation_journal,
    operation_from_action_result,
    record_action_result,
)


def test_append_operation_persists_newest_record_first(tmp_path: Path) -> None:
    first = V2Operation(
        id="service:restart",
        name="Restart",
        kind="service.restart",
        status="succeeded",
        health=V2Health(state="ok", message="done"),
        target=V2ResourceRef(kind="service", id="phlo-api", label="phlo-api"),
        metadata={"unsafe_url": "http://internal", "safe_count": 1},
    )
    second = first.model_copy(update={"id": "service:stop", "name": "Stop"})

    append_operation(
        tmp_path,
        first,
        record_id="op-first",
        recorded_at="2026-05-16T10:00:00+00:00",
    )
    append_operation(
        tmp_path,
        second,
        record_id="op-second",
        recorded_at="2026-05-16T10:01:00+00:00",
    )

    records = load_operation_journal(tmp_path)

    assert [record.id for record in records] == ["op-second", "op-first"]
    assert records[0].metadata["original_operation_id"] == "service:stop"
    assert records[1].metadata["safe_count"] == 1
    assert "unsafe_url" not in records[1].metadata


def test_operation_from_action_result_creates_skipped_operation() -> None:
    action = V2Action(
        id="quality:raw.orders:rerun",
        label="Re-run quality check",
        kind="quality.rerun",
        enabled=False,
        reason="Quality re-runs need a provider-backed execution contract.",
        required_capability="quality_backend",
    )
    result = V2ActionResult(
        action=action,
        status="skipped",
        message="Quality re-runs need a provider-backed execution contract.",
    )

    operation = operation_from_action_result(
        result,
        target=V2ResourceRef(kind="quality", id="raw.orders", label="raw.orders"),
    )

    assert operation.id == "quality:raw.orders:rerun"
    assert operation.name == "Re-run quality check"
    assert operation.kind == "quality.rerun"
    assert operation.status == "skipped"
    assert operation.health.state == "warning"
    assert operation.target is not None
    assert operation.target.kind == "quality"
    assert operation.metadata["action_id"] == "quality:raw.orders:rerun"


def test_record_action_result_returns_result_with_recorded_operation(tmp_path: Path) -> None:
    action = V2Action(
        id="unsupported:thing",
        label="Unsupported action",
        kind="unsupported",
        enabled=False,
    )
    result = V2ActionResult(
        action=action,
        status="failed",
        message="Unsupported Observatory v2 action: unsupported:thing",
    )

    recorded_result = record_action_result(
        tmp_path,
        result,
        record_id="op-recorded",
        recorded_at="2026-05-16T11:00:00+00:00",
    )

    assert recorded_result.operation is not None
    assert recorded_result.operation.id == "op-recorded"
    assert recorded_result.operation.status == "failed"
    assert load_operation_journal(tmp_path)[0].id == "op-recorded"
