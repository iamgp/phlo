"""Provider-neutral models for durable pipeline run evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

RUN_EVIDENCE_SCHEMA_VERSION = 1


def _now() -> datetime:
    return datetime.now(UTC)


class EvidenceCompleteness(StrEnum):
    """Evidence availability, kept separate from the run outcome."""

    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    MISSING = "missing"
    EXPIRED = "expired"
    REDACTED = "redacted"


@dataclass(frozen=True, slots=True)
class PipelineRun:
    """Authoritative project-scoped record for one pipeline execution."""

    project_id: str
    run_id: str
    pipeline_name: str | None = None
    provider_run_id: str | None = None
    trigger: str | None = None
    initiator: str | None = None
    effective_identity: str | None = None
    partition_key: str | None = None
    code_version: str | None = None
    config_version: str | None = None
    attempt: int = 1
    trace_id: str | None = None
    status: str = "running"
    started_at: datetime = field(default_factory=_now)
    finished_at: datetime | None = None
    failure_summary: str | None = None
    evidence_completeness: EvidenceCompleteness = EvidenceCompleteness.INCOMPLETE


@dataclass(frozen=True, slots=True)
class RunEvent:
    """Immutable lifecycle event with producer-scoped idempotency identity."""

    project_id: str
    run_id: str
    event_id: str
    event_type: str
    producer: str
    payload: dict[str, Any]
    stage_id: str | None = None
    schema_version: str = "1.0"
    observed_at: datetime = field(default_factory=_now)
    sequence: int | None = None


@dataclass(frozen=True, slots=True)
class RunStage:
    """Observed lifecycle stage within a pipeline run."""

    project_id: str
    run_id: str
    stage_id: str
    stage_type: str = "unknown"
    provider: str | None = None
    tool: str | None = None
    asset: str | None = None
    attempt: int = 1
    status: str = "unknown"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass(frozen=True, slots=True)
class RunResource:
    """Input, staged, or output resource observed by a run."""

    project_id: str
    run_id: str
    resource_id: str
    resource_kind: str = "unknown"
    role: str = "unknown"
    normalized_identity: str | None = None
    uri: str | None = None
    table_name: str | None = None
    catalog: str | None = None
    ref_name: str | None = None
    schema_hash: str | None = None
    watermark: str | None = None
    record_count: int | None = None
    byte_count: int | None = None
    staged_objects: list[str] = field(default_factory=list)
    snapshot_before: str | None = None
    snapshot_after: str | None = None


@dataclass(frozen=True, slots=True)
class RunLineageEdge:
    """Historical lineage edge observed or declared for one run."""

    project_id: str
    run_id: str
    source: str
    target: str
    lineage_edge_id: str
    column_mapping: dict[str, Any] = field(default_factory=dict)
    origin: str = "observed"
    derivation: str = "exact"
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class RunQualityResult:
    """One quality result correlated to its run and optional stage."""

    project_id: str
    run_id: str
    quality_result_id: str
    check_id: str
    asset: str | None = None
    stage_id: str | None = None
    severity: str | None = None
    blocking: bool = False
    passed: bool = False
    evaluated_count: int | None = None
    failed_count: int | None = None
    failure_artifact_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RunCatalogChange:
    """Catalog/WAP change associated with a run."""

    project_id: str
    run_id: str
    catalog_change_id: str
    operation: str
    catalog_ref: str | None = None
    content_key: str | None = None
    source_hash: str | None = None
    target_hash: str | None = None
    commit_hash: str | None = None
    commit_message: str | None = None
    merge_outcome: str | None = None
    snapshot_before: str | None = None
    snapshot_after: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RunArtifact:
    """Durable identity for an artifact even after its content expires."""

    project_id: str
    run_id: str
    artifact_id: str
    artifact_kind: str
    uri: str | None = None
    content_type: str | None = None
    checksum: str | None = None
    retention_class: str | None = None
    expires_at: datetime | None = None
    legal_hold: bool = False
    status: EvidenceCompleteness = EvidenceCompleteness.COMPLETE
