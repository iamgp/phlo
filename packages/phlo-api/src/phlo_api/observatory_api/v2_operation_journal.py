"""Persistent operation journal for Observatory v2."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import cast
from uuid import uuid4

from phlo_api.observatory_api.v2_metadata import safe_metadata
from phlo_api.observatory_api.v2_models import (
    HealthState,
    OperationStatus,
    V2ActionResult,
    V2Health,
    V2Operation,
    V2ResourceRef,
)

MAX_OPERATION_RECORDS = 200


def operation_journal_path(project_root: Path) -> Path:
    state_dir = project_root / ".phlo" / "observatory-v2"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / "operation_journal.json"


def load_operation_journal(project_root: Path) -> list[V2Operation]:
    path = operation_journal_path(project_root)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    items = payload.get("items") if isinstance(payload, Mapping) else None
    if not isinstance(items, list):
        return []

    operations: list[V2Operation] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        try:
            operations.append(V2Operation.model_validate(item))
        except Exception:
            continue
    return sort_operations(operations)


def write_operation_journal(project_root: Path, operations: Iterable[V2Operation]) -> None:
    records = sort_operations(list(operations))[:MAX_OPERATION_RECORDS]
    operation_journal_path(project_root).write_text(
        json.dumps({"items": [operation.model_dump() for operation in records]}, indent=2),
        encoding="utf-8",
    )


def append_operation(
    project_root: Path,
    operation: V2Operation,
    *,
    record_id: str | None = None,
    recorded_at: str | None = None,
) -> V2Operation:
    timestamp = recorded_at or datetime.now(UTC).isoformat()
    original_id = operation.id
    metadata = safe_metadata(
        {
            **operation.metadata,
            "original_operation_id": original_id,
            "recorded_at": timestamp,
        }
    )
    recorded = operation.model_copy(
        update={
            "id": record_id or f"op-{uuid4().hex[:12]}",
            "started_at": operation.started_at or timestamp,
            "completed_at": operation.completed_at or timestamp,
            "duration_seconds": operation.duration_seconds
            if operation.duration_seconds is not None
            else 0.0,
            "metadata": metadata,
        }
    )
    write_operation_journal(project_root, [recorded, *load_operation_journal(project_root)])
    return recorded


def record_action_result(
    project_root: Path,
    result: V2ActionResult,
    *,
    target: V2ResourceRef | None = None,
    record_id: str | None = None,
    recorded_at: str | None = None,
) -> V2ActionResult:
    operation = result.operation or operation_from_action_result(result, target=target)
    recorded = append_operation(
        project_root,
        operation,
        record_id=record_id,
        recorded_at=recorded_at,
    )
    return result.model_copy(update={"operation": recorded})


def operation_from_action_result(
    result: V2ActionResult,
    *,
    target: V2ResourceRef | None = None,
) -> V2Operation:
    action = result.action
    return V2Operation(
        id=action.id,
        name=action.label,
        kind=action.kind,
        status=result.status,
        health=V2Health(
            state=_health_state_for_action_status(result.status),
            message=result.message[:200],
        ),
        target=target,
        metadata=safe_metadata(
            {
                "action_id": action.id,
                "action_kind": action.kind,
                "risk_level": action.risk_level,
                "required_capability": action.required_capability,
                "required_service": action.required_service,
                "message": result.message,
            }
        ),
    )


def operation_from_workflow_action(
    *,
    action_id: str,
    status: str,
    message: str,
    files: list[str],
) -> V2Operation:
    return V2Operation(
        id=f"workflow:{action_id}",
        name="Apply workflow proposal",
        kind="workflow.apply",
        status=_coerce_operation_status(status),
        health=V2Health(
            state=_health_state_for_action_status(status),
            message=message[:200],
        ),
        target=V2ResourceRef(kind="workflow", id=action_id, label=action_id),
        metadata=safe_metadata(
            {
                "action_id": action_id,
                "files": files,
                "message": message,
            }
        ),
    )


def sort_operations(operations: Iterable[V2Operation]) -> list[V2Operation]:
    return sorted(operations, key=_operation_sort_key, reverse=True)


def _operation_sort_key(operation: V2Operation) -> tuple[str, str]:
    timestamp = operation.completed_at or operation.started_at or ""
    return (timestamp, operation.id)


def _health_state_for_action_status(status: str) -> HealthState:
    if status == "succeeded":
        return "ok"
    if status == "failed":
        return "error"
    if status == "skipped":
        return "warning"
    return "unknown"


def _coerce_operation_status(status: str) -> OperationStatus:
    if status in {"queued", "running", "succeeded", "failed", "skipped", "unknown"}:
        return cast(OperationStatus, status)
    return "unknown"
