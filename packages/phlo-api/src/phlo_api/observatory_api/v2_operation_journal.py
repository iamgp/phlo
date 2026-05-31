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
OPERATION_OBSERVABILITY_SCHEMA_VERSION = "phlo.operation_observability.v1"


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
    operation_id = record_id or f"op-{uuid4().hex[:12]}"
    metadata = safe_metadata(
        {
            **operation.metadata,
            "original_operation_id": original_id,
            "recorded_at": timestamp,
        }
    )
    metadata["observability_contract"] = _operation_observability_contract(
        operation,
        operation_id=operation_id,
        original_operation_id=original_id,
    )
    recorded = operation.model_copy(
        update={
            "id": operation_id,
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


def build_operation_observability_context(operation: V2Operation) -> dict[str, object]:
    """Build the stable agent-readable observability context for an operation."""
    identifiers = _contract_from_operation(operation)
    status = (
        "open" if operation.status in {"failed", "running", "queued", "unknown"} else "resolved"
    )
    return {
        "schema_version": OPERATION_OBSERVABILITY_SCHEMA_VERSION,
        "operation": {
            "id": operation.id,
            "name": operation.name,
            "kind": operation.kind,
            "status": operation.status,
            "health": operation.health.model_dump(mode="json"),
            "target": operation.target.model_dump(mode="json") if operation.target else None,
            "started_at": operation.started_at,
            "completed_at": operation.completed_at,
            "duration_seconds": operation.duration_seconds,
        },
        "identifiers": identifiers,
        "incident": {
            "status": status,
            "severity": operation.health.state,
            "message": operation.health.message or operation.metadata.get("message"),
            "incident_ids": identifiers["incident_ids"],
        },
        "retention": {
            "history_limit": MAX_OPERATION_RECORDS,
            "history_store": ".phlo/observatory-v2/operation_journal.json",
        },
        "metadata": safe_metadata(operation.metadata),
    }


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


def _operation_observability_contract(
    operation: V2Operation,
    *,
    operation_id: str,
    original_operation_id: str | None = None,
) -> dict[str, object]:
    return {
        "schema_version": OPERATION_OBSERVABILITY_SCHEMA_VERSION,
        "operation_id": operation_id,
        "original_operation_id": original_operation_id or operation.id,
        "trace_ids": _identifier_values(operation.metadata, "trace"),
        "log_ids": _identifier_values(operation.metadata, "log"),
        "metric_ids": _identifier_values(operation.metadata, "metric"),
        "incident_ids": _identifier_values(operation.metadata, "incident"),
    }


def _contract_from_operation(operation: V2Operation) -> dict[str, object]:
    raw_contract = operation.metadata.get("observability_contract")
    if isinstance(raw_contract, Mapping):
        return {
            "operation_id": _string_or_default(raw_contract.get("operation_id"), operation.id),
            "trace_ids": _string_list(raw_contract.get("trace_ids")),
            "log_ids": _string_list(raw_contract.get("log_ids")),
            "metric_ids": _string_list(raw_contract.get("metric_ids")),
            "incident_ids": _string_list(raw_contract.get("incident_ids")),
        }
    contract = _operation_observability_contract(operation, operation_id=operation.id)
    return {
        "operation_id": operation.id,
        "trace_ids": contract["trace_ids"],
        "log_ids": contract["log_ids"],
        "metric_ids": contract["metric_ids"],
        "incident_ids": contract["incident_ids"],
    }


def _identifier_values(metadata: Mapping[str, object], family: str) -> list[str]:
    keys = (f"{family}_id", f"{family}_ids", f"{family}s", f"phlo.{family}_id")
    values: list[str] = []
    for key in keys:
        values.extend(_string_list(metadata.get(key)))
    return sorted(dict.fromkeys(values))


def _string_list(value: object) -> list[str]:
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, Iterable) and not isinstance(value, str | bytes | Mapping):
        return [item for item in (_string_or_default(raw, "") for raw in value) if item]
    return []


def _string_or_default(value: object, default: str) -> str:
    if isinstance(value, str) and value:
        return value
    return default


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
