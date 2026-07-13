"""Core hook sink that records correlated lifecycle events."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from typing import Any

from phlo.hooks.events import (
    HookEvent,
    IngestionEvent,
    LineageEvent,
    PublishEvent,
    QualityResultEvent,
    TransformEvent,
)
from phlo.plugins.hooks import FailurePolicy, HookFilter, HookRegistration
from phlo.run_evidence.models import (
    PipelineRun,
    RunEvent,
    RunLineageEdge,
    RunQualityResult,
    RunStage,
)
from phlo.run_evidence.store import (
    _SqlRunEvidenceStore,
    default_run_evidence_store,
)

_LIFECYCLE_EVENT_TYPES = {
    "run.start",
    "run.end",
    "run.heartbeat",
    "ingestion.start",
    "ingestion.end",
    "transform.start",
    "transform.end",
    "quality.result",
    "publish.start",
    "publish.end",
    "lineage.edges",
}


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("\x00".join(parts).encode("utf-8")).hexdigest()[:32]


class CoreRunEvidenceHookProvider:
    """Persist the provider-neutral lifecycle events already emitted by Phlo."""

    def __init__(self, store: _SqlRunEvidenceStore | None = None) -> None:
        self._store = store

    def get_hooks(self) -> list[HookRegistration]:
        return [
            HookRegistration(
                hook_name="core_run_evidence",
                handler=self._handle_event,
                priority=0,
                filters=HookFilter(event_types=set(_LIFECYCLE_EVENT_TYPES)),
                failure_policy=FailurePolicy.RAISE,
            )
        ]

    def _handle_event(self, event: HookEvent) -> None:
        project_id, run_id = _event_correlation(event)
        if run_id is None:
            # Legacy hook callers can emit uncorrelated events. They cannot be
            # safely attached to a durable run and are intentionally skipped.
            return
        if project_id is None:
            # A run ID without its project is an incomplete correlation, not a
            # tenant identity. Keep legacy hook callers operational while
            # refusing to persist evidence that cannot satisfy the composite
            # tenant keys in the store.
            return

        store = self._store or default_run_evidence_store()
        self._store = store
        run = PipelineRun(
            project_id=project_id,
            run_id=run_id,
            pipeline_name=event.correlation.job_name,
            provider_run_id=run_id,
            partition_key=event.correlation.partition_key,
            trace_id=event.correlation.trace_id,
            status=_run_status(event),
            attempt=event.correlation.attempt,
        )
        stage = _stage_for_event(event, project_id=project_id, run_id=run_id)
        quality_result = _quality_for_event(
            event, project_id=project_id, run_id=run_id, stage=stage
        )
        lineage_edges = _lineage_for_event(event, project_id=project_id, run_id=run_id)
        store.append_event(
            RunEvent(
                project_id=project_id,
                run_id=run_id,
                event_id=event.event_id,
                event_type=event.event_type,
                producer=event.producer,
                schema_version=event.version,
                observed_at=event.timestamp,
                payload=_event_payload(event),
                stage_id=stage.stage_id if stage else None,
                attempt=event.correlation.attempt,
            ),
            run=run,
            stage=stage,
            quality_result=quality_result,
            lineage_edges=tuple(lineage_edges),
        )


def _event_correlation(event: HookEvent) -> tuple[str | None, str | None]:
    project_id = event.correlation.project_id
    run_id = event.correlation.run_id or getattr(event, "run_id", None)
    event_run_id = getattr(event, "run_id", None)
    if event_run_id is not None and event.correlation.run_id not in (None, event_run_id):
        raise ValueError("event run_id and correlation.run_id do not match")
    return project_id, run_id


def _event_payload(event: HookEvent) -> dict[str, Any]:
    """Keep envelope identity/time in columns so retries hash logical content."""
    payload = asdict(event)
    payload.pop("event_id", None)
    payload.pop("timestamp", None)
    correlation = payload.get("correlation")
    if isinstance(correlation, dict):
        payload["correlation"] = {
            key: correlation.get(key)
            for key in (
                "project_id",
                "run_id",
                "attempt",
                "asset_key",
                "job_name",
                "partition_key",
                "check_name",
            )
        }
    return payload


def _stage_for_event(event: HookEvent, *, project_id: str, run_id: str) -> RunStage | None:
    stage_type = _stage_type(event)
    if stage_type is None:
        return None
    asset = getattr(event, "asset_key", None)
    check_name = getattr(event, "check_name", None)
    stage_key = check_name or asset or getattr(event.correlation, "job_name", None) or stage_type
    stage_id = _stable_id(
        project_id, run_id, str(event.correlation.attempt), stage_type, str(stage_key)
    )
    status = getattr(event, "status", None) or "observed"
    if status in {"started", "start", "running"}:
        status = "running"
    return RunStage(
        project_id=project_id,
        run_id=run_id,
        stage_id=stage_id,
        stage_type=stage_type,
        provider="hook",
        tool=getattr(event, "tool", None) or getattr(event, "target_system", None),
        asset=asset,
        status=status,
        attempt=event.correlation.attempt,
        started_at=event.timestamp,
        finished_at=event.timestamp if status not in {"running", "observed"} else None,
        metrics=getattr(event, "metrics", {}) or {},
        error=getattr(event, "error", None),
    )


def _quality_for_event(
    event: HookEvent,
    *,
    project_id: str,
    run_id: str,
    stage: RunStage | None,
) -> RunQualityResult | None:
    if not isinstance(event, QualityResultEvent):
        return None
    metadata = event.metadata or {}
    return RunQualityResult(
        project_id=project_id,
        run_id=run_id,
        quality_result_id=_stable_id(
            project_id, run_id, str(event.correlation.attempt), "quality", event.check_name
        ),
        check_id=event.check_name,
        asset=event.asset_key,
        stage_id=stage.stage_id if stage else None,
        severity=event.severity,
        blocking=event.severity in {"error", "critical"},
        passed=event.passed,
        evaluated_count=_as_int(metadata.get("evaluated_count", metadata.get("total_rows"))),
        failed_count=_as_int(metadata.get("failed_count", metadata.get("failed_rows"))),
        metadata=metadata,
        attempt=event.correlation.attempt,
    )


def _lineage_for_event(
    event: HookEvent,
    *,
    project_id: str,
    run_id: str,
) -> list[RunLineageEdge]:
    if not isinstance(event, LineageEvent):
        return []
    metadata = event.metadata or {}
    return [
        RunLineageEdge(
            project_id=project_id,
            run_id=run_id,
            lineage_edge_id=_stable_id(project_id, run_id, event.event_id, str(index)),
            source=source,
            target=target,
            column_mapping=metadata.get("column_mapping", {}),
            origin=str(metadata.get("origin", "observed")),
            derivation=str(metadata.get("derivation", "exact")),
            confidence=_as_float(metadata.get("confidence")),
        )
        for index, (source, target) in enumerate(event.edges)
    ]


def _stage_type(event: HookEvent) -> str | None:
    if isinstance(event, IngestionEvent):
        return "ingest"
    if isinstance(event, TransformEvent):
        return "transform"
    if isinstance(event, QualityResultEvent):
        return "check"
    if isinstance(event, PublishEvent):
        return "publish"
    if isinstance(event, LineageEvent):
        return "lineage"
    return None


def _run_status(event: HookEvent) -> str:
    if event.event_type not in {"run.end", "run.terminal"}:
        return "running"
    status = getattr(event, "status", None)
    if status in {"success", "failed", "error", "cancelled", "canceled", "skipped"}:
        return str(status)
    return "running"


def _as_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
