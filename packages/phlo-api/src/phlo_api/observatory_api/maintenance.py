"""Maintenance API Router.

Endpoints for Iceberg maintenance observability data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

router = APIRouter(tags=["maintenance"])


class MaintenanceOperationStatus(BaseModel):
    operation: str
    namespace: str
    ref: str
    status: str
    completed_at: str
    duration_seconds: float | None
    tables_processed: int
    errors: int
    snapshots_deleted: int
    orphan_files: int
    total_records: int
    total_size_mb: float
    dry_run: bool | None = None
    run_id: str | None = None
    job_name: str | None = None


class MaintenanceStatusSnapshot(BaseModel):
    last_updated: str
    operations: list[MaintenanceOperationStatus]


@router.get("/status", response_model=MaintenanceStatusSnapshot | dict)
def get_maintenance_status() -> MaintenanceStatusSnapshot | dict[str, str]:
    """Get maintenance status derived from telemetry logs."""

    try:
        from phlo_metrics.maintenance import load_maintenance_status

        snapshot = load_maintenance_status()
        return _serialize_snapshot(snapshot)
    except Exception as exc:
        return {"error": str(exc)}


@router.get("/metrics", response_class=PlainTextResponse)
def get_maintenance_metrics() -> PlainTextResponse:
    """Expose maintenance metrics in Prometheus text format."""

    try:
        from phlo_metrics.maintenance import render_maintenance_prometheus

        return PlainTextResponse(render_maintenance_prometheus())
    except Exception as exc:
        return PlainTextResponse(f"# error: {exc}\n", status_code=500)


def _serialize_snapshot(snapshot: Any) -> MaintenanceStatusSnapshot:
    return MaintenanceStatusSnapshot(
        last_updated=_isoformat(snapshot.last_updated),
        operations=[_serialize_operation(op) for op in snapshot.operations],
    )


def _serialize_operation(operation: Any) -> MaintenanceOperationStatus:
    return MaintenanceOperationStatus(
        operation=operation.operation,
        namespace=operation.namespace,
        ref=operation.ref,
        status=operation.status,
        completed_at=_isoformat(operation.completed_at),
        duration_seconds=operation.duration_seconds,
        tables_processed=operation.tables_processed,
        errors=operation.errors,
        snapshots_deleted=operation.snapshots_deleted,
        orphan_files=operation.orphan_files,
        total_records=operation.total_records,
        total_size_mb=operation.total_size_mb,
        dry_run=operation.dry_run,
        run_id=operation.run_id,
        job_name=operation.job_name,
    )


def _isoformat(value: datetime | Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)
