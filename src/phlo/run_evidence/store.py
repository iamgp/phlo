"""Transactional stores for the run-evidence contract."""

from __future__ import annotations

import os
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from phlo.run_evidence.models import (
    EvidenceCompleteness,
    PipelineRun,
    RunArtifact,
    RunCatalogChange,
    RunEvent,
    RunLineageEdge,
    RunQualityResult,
    RunResource,
    RunStage,
)
from phlo.run_evidence.redaction import canonical_json, payload_checksum, redact_payload


class IdempotencyConflict(ValueError):
    """A producer reused an event identity with different content."""


def _timestamp(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _json(value: Any) -> str:
    return canonical_json(value)


def _text(value: str | None) -> str | None:
    redacted = redact_payload(value)
    return redacted if isinstance(redacted, str) or redacted is None else str(redacted)


class _SqlRunEvidenceStore:
    """Shared SQL implementation; subclasses provide transaction connections."""

    placeholder = "?"
    table_prefix = ""

    def __init__(self) -> None:
        self._initialized = False
        self._lock = threading.RLock()

    def _connect(self) -> Any:
        raise NotImplementedError

    def _close_connection(self, connection: Any) -> None:
        connection.close()

    def _table(self, name: str) -> str:
        return f"{self.table_prefix}{name}"

    @contextmanager
    def _transaction(self) -> Iterator[tuple[Any, Any]]:
        self._ensure_schema()
        with self._lock:
            connection = self._connect()
            cursor = connection.cursor()
            try:
                if self.placeholder == "?":
                    cursor.execute("BEGIN IMMEDIATE")
                yield connection, cursor
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
                self._close_connection(connection)

    def _ensure_schema(self) -> None:
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return
            self._initialize_schema()
            self._initialized = True

    def _initialize_schema(self) -> None:
        raise NotImplementedError

    def append_pipeline_run(self, run: PipelineRun) -> None:
        with self._transaction() as (_, cursor):
            self._upsert_run(cursor, run)

    def append_event(
        self,
        event: RunEvent,
        *,
        run: PipelineRun | None = None,
        stage: RunStage | None = None,
        quality_result: RunQualityResult | None = None,
        lineage_edges: tuple[RunLineageEdge, ...] = (),
    ) -> bool:
        """Append one event and optional derived records in one transaction."""
        with self._transaction() as (_, cursor):
            cursor.execute(
                f"SELECT 1 FROM {self._table('run_event')} "
                f"WHERE project_id = {self.placeholder} AND producer = {self.placeholder} "
                f"AND event_id = {self.placeholder}",
                (event.project_id, event.producer, event.event_id),
            )
            event_exists = cursor.fetchone() is not None
            if run is not None and not event_exists:
                self._upsert_run(cursor, run)
            inserted = self._insert_event(cursor, event)
            if inserted:
                if stage is not None:
                    self._insert_stage(cursor, stage)
                if quality_result is not None:
                    self._insert_quality(cursor, quality_result)
                for edge in lineage_edges:
                    self._insert_lineage(cursor, edge)
            return inserted

    def append_stage(self, stage: RunStage) -> None:
        with self._transaction() as (_, cursor):
            self._insert_stage(cursor, stage)

    def append_resource(self, resource: RunResource) -> None:
        with self._transaction() as (_, cursor):
            self._insert_resource(cursor, resource)

    def append_lineage_edge(self, edge: RunLineageEdge) -> None:
        with self._transaction() as (_, cursor):
            self._insert_lineage(cursor, edge)

    def append_quality_result(self, result: RunQualityResult) -> None:
        with self._transaction() as (_, cursor):
            self._insert_quality(cursor, result)

    def append_catalog_change(self, change: RunCatalogChange) -> None:
        with self._transaction() as (_, cursor):
            self._insert_catalog_change(cursor, change)

    def append_artifact(self, artifact: RunArtifact) -> None:
        with self._transaction() as (_, cursor):
            self._insert_artifact(cursor, artifact)

    def update_run(
        self,
        project_id: str,
        run_id: str,
        *,
        status: str | None = None,
        finished_at: datetime | None = None,
        failure_summary: str | None = None,
        evidence_completeness: EvidenceCompleteness | None = None,
    ) -> None:
        """Update terminal run state without changing its identity or history."""
        fields: list[str] = []
        values: list[Any] = []
        if status is not None:
            fields.append("status = " + self.placeholder)
            values.append(status)
        if finished_at is not None:
            fields.append("finished_at = " + self.placeholder)
            values.append(_timestamp(finished_at))
        if failure_summary is not None:
            fields.append("failure_summary = " + self.placeholder)
            values.append(_text(failure_summary))
        if evidence_completeness is not None:
            fields.append("evidence_completeness = " + self.placeholder)
            values.append(evidence_completeness.value)
        if not fields:
            return
        fields.append("updated_at = " + self.placeholder)
        values.append(_timestamp(datetime.now(UTC)))
        values.extend([project_id, run_id])
        with self._transaction() as (_, cursor):
            cursor.execute(
                f"UPDATE {self._table('pipeline_run')} SET {', '.join(fields)} "
                f"WHERE project_id = {self.placeholder} AND run_id = {self.placeholder}",
                tuple(values),
            )

    def get_run(self, project_id: str, run_id: str) -> dict[str, Any] | None:
        with self._transaction() as (_, cursor):
            cursor.execute(
                f"SELECT * FROM {self._table('pipeline_run')} "
                f"WHERE project_id = {self.placeholder} AND run_id = {self.placeholder}",
                (project_id, run_id),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return self._row_dict(cursor, row)

    def list_events(self, project_id: str, run_id: str) -> list[dict[str, Any]]:
        with self._transaction() as (_, cursor):
            cursor.execute(
                f"SELECT * FROM {self._table('run_event')} "
                f"WHERE project_id = {self.placeholder} AND run_id = {self.placeholder} "
                "ORDER BY observed_at, id",
                (project_id, run_id),
            )
            return [self._row_dict(cursor, row) for row in cursor.fetchall()]

    def count_events(self, project_id: str, run_id: str) -> int:
        with self._transaction() as (_, cursor):
            cursor.execute(
                f"SELECT COUNT(*) FROM {self._table('run_event')} "
                f"WHERE project_id = {self.placeholder} AND run_id = {self.placeholder}",
                (project_id, run_id),
            )
            return int(cursor.fetchone()[0])

    def _upsert_run(self, cursor: Any, run: PipelineRun) -> None:
        cursor.execute(
            f"SELECT project_id FROM {self._table('pipeline_run')} "
            f"WHERE project_id = {self.placeholder} AND run_id = {self.placeholder}",
            (run.project_id, run.run_id),
        )
        columns = (
            "run_id, project_id, pipeline_name, provider_run_id, trigger, initiator, "
            "effective_identity, partition_key, code_version, config_version, attempt, "
            "trace_id, status, started_at, finished_at, failure_summary, evidence_completeness"
        )
        values = (
            run.run_id,
            run.project_id,
            _text(run.pipeline_name),
            _text(run.provider_run_id),
            _text(run.trigger),
            _text(run.initiator),
            _text(run.effective_identity),
            _text(run.partition_key),
            _text(run.code_version),
            _text(run.config_version),
            run.attempt,
            _text(run.trace_id),
            _text(run.status),
            _timestamp(run.started_at),
            _timestamp(run.finished_at),
            _text(run.failure_summary),
            run.evidence_completeness.value,
        )
        updates = ", ".join(
            [
                f"{field} = COALESCE(existing_run.{field}, EXCLUDED.{field})"
                for field in (
                    "pipeline_name",
                    "provider_run_id",
                    "trigger",
                    "initiator",
                    "partition_key",
                )
            ]
            + [
                # provider_run_id identifies the logical provider run, while
                # these fields describe the latest execution attempt. A
                # same-attempt replay only fills a missing value so late
                # lower-attempt evidence cannot rewrite current provenance.
                "effective_identity = CASE WHEN EXCLUDED.attempt > existing_run.attempt "
                "THEN EXCLUDED.effective_identity WHEN EXCLUDED.attempt < existing_run.attempt "
                "THEN existing_run.effective_identity ELSE COALESCE(existing_run.effective_identity, EXCLUDED.effective_identity) END",
                "code_version = CASE WHEN EXCLUDED.attempt > existing_run.attempt "
                "THEN EXCLUDED.code_version WHEN EXCLUDED.attempt < existing_run.attempt "
                "THEN existing_run.code_version ELSE COALESCE(existing_run.code_version, EXCLUDED.code_version) END",
                "config_version = CASE WHEN EXCLUDED.attempt > existing_run.attempt "
                "THEN EXCLUDED.config_version WHEN EXCLUDED.attempt < existing_run.attempt "
                "THEN existing_run.config_version ELSE COALESCE(existing_run.config_version, EXCLUDED.config_version) END",
                "started_at = CASE WHEN EXCLUDED.attempt > existing_run.attempt "
                "THEN EXCLUDED.started_at WHEN EXCLUDED.attempt < existing_run.attempt "
                "THEN existing_run.started_at ELSE COALESCE(existing_run.started_at, EXCLUDED.started_at) END",
                "attempt = CASE WHEN existing_run.attempt > EXCLUDED.attempt "
                "THEN existing_run.attempt ELSE EXCLUDED.attempt END",
                "status = CASE WHEN EXCLUDED.attempt > existing_run.attempt "
                "THEN EXCLUDED.status WHEN EXCLUDED.attempt < existing_run.attempt "
                "THEN existing_run.status WHEN existing_run.status IN "
                "('success', 'failed', 'error', 'cancelled', 'canceled', 'skipped') "
                "THEN existing_run.status ELSE EXCLUDED.status END",
                "trace_id = CASE WHEN EXCLUDED.attempt > existing_run.attempt "
                "THEN EXCLUDED.trace_id WHEN EXCLUDED.attempt < existing_run.attempt "
                "THEN existing_run.trace_id ELSE COALESCE(existing_run.trace_id, EXCLUDED.trace_id) END",
                "finished_at = CASE WHEN EXCLUDED.attempt > existing_run.attempt "
                "THEN EXCLUDED.finished_at WHEN EXCLUDED.attempt < existing_run.attempt "
                "THEN existing_run.finished_at WHEN existing_run.status IN "
                "('success', 'failed', 'error', 'cancelled', 'canceled', 'skipped') "
                "THEN COALESCE(existing_run.finished_at, EXCLUDED.finished_at) "
                "ELSE COALESCE(EXCLUDED.finished_at, existing_run.finished_at) END",
                "failure_summary = CASE WHEN EXCLUDED.attempt > existing_run.attempt "
                "THEN EXCLUDED.failure_summary WHEN EXCLUDED.attempt < existing_run.attempt "
                "THEN existing_run.failure_summary WHEN existing_run.status IN "
                "('success', 'failed', 'error', 'cancelled', 'canceled', 'skipped') "
                "THEN COALESCE(existing_run.failure_summary, EXCLUDED.failure_summary) "
                "ELSE COALESCE(EXCLUDED.failure_summary, existing_run.failure_summary) END",
                "evidence_completeness = CASE WHEN EXCLUDED.attempt > existing_run.attempt "
                "THEN EXCLUDED.evidence_completeness WHEN EXCLUDED.attempt < existing_run.attempt "
                "THEN existing_run.evidence_completeness WHEN existing_run.status IN "
                "('success', 'failed', 'error', 'cancelled', 'canceled', 'skipped') "
                "THEN existing_run.evidence_completeness WHEN existing_run.evidence_completeness IN "
                "('complete', 'expired', 'redacted') AND EXCLUDED.evidence_completeness = 'incomplete' "
                "THEN existing_run.evidence_completeness ELSE EXCLUDED.evidence_completeness END",
            ]
        )
        cursor.execute(
            f"INSERT INTO {self._table('pipeline_run')} AS existing_run ({columns}) VALUES "
            f"({', '.join([self.placeholder] * len(values))}) "
            f"ON CONFLICT (project_id, run_id) DO UPDATE SET {updates}, "
            "updated_at = CURRENT_TIMESTAMP",
            values,
        )

    def _insert_event(self, cursor: Any, event: RunEvent) -> bool:
        self._require_id("event_id", event.event_id)
        self._require_id("producer", event.producer)
        redacted = redact_payload(event.payload)
        checksum = payload_checksum(redacted)
        values = (
            event.project_id,
            event.run_id,
            event.stage_id,
            event.event_id,
            event.event_type,
            event.schema_version,
            event.producer,
            _timestamp(event.observed_at),
            event.sequence,
            _json(redacted),
            checksum,
        )
        cursor.execute(
            f"INSERT INTO {self._table('run_event')} "
            "(project_id, run_id, stage_id, event_id, event_type, schema_version, producer, "
            "observed_at, sequence, payload, payload_checksum) VALUES ("
            + ", ".join([self.placeholder] * len(values))
            + ") ON CONFLICT (project_id, producer, event_id) DO NOTHING",
            values,
        )
        inserted = cursor.rowcount == 1
        cursor.execute(
            f"SELECT project_id, run_id, payload_checksum FROM {self._table('run_event')} "
            f"WHERE project_id = {self.placeholder} AND producer = {self.placeholder} "
            f"AND event_id = {self.placeholder}",
            (event.project_id, event.producer, event.event_id),
        )
        existing = cursor.fetchone()
        if existing is None:
            raise RuntimeError("event insert did not return a durable record")
        if existing[0] != event.project_id or existing[1] != event.run_id:
            raise IdempotencyConflict(
                f"event {event.producer}/{event.event_id} is correlated to another run"
            )
        if existing[2] != checksum:
            raise IdempotencyConflict(
                f"event {event.producer}/{event.event_id} was replayed with different payload"
            )
        return inserted

    def _insert_stage(self, cursor: Any, stage: RunStage) -> None:
        self._require_id("stage_id", stage.stage_id)
        immutable_checksum = payload_checksum(
            {
                "stage_id": stage.stage_id,
                "project_id": stage.project_id,
                "run_id": stage.run_id,
                "stage_type": stage.stage_type,
                "provider": stage.provider,
                "tool": stage.tool,
                "asset": stage.asset,
                "attempt": stage.attempt,
            }
        )
        values = (
            stage.stage_id,
            stage.project_id,
            stage.run_id,
            stage.stage_type,
            _text(stage.provider),
            _text(stage.tool),
            _text(stage.asset),
            stage.attempt,
            stage.status,
            _timestamp(stage.started_at),
            _timestamp(stage.finished_at),
            _json(stage.metrics),
            _text(stage.error),
            immutable_checksum,
        )
        cursor.execute(
            f"INSERT INTO {self._table('run_stage')} "
            "(stage_id, project_id, run_id, stage_type, provider, tool, asset, attempt, status, "
            "started_at, finished_at, metrics, error, record_checksum) VALUES ("
            + ", ".join([self.placeholder] * len(values))
            + ") ON CONFLICT (project_id, run_id, stage_id) DO NOTHING",
            values,
        )
        if cursor.rowcount == 1:
            return
        cursor.execute(
            f"SELECT run_id, record_checksum FROM {self._table('run_stage')} "
            f"WHERE project_id = {self.placeholder} AND run_id = {self.placeholder} "
            f"AND stage_id = {self.placeholder}",
            (stage.project_id, stage.run_id, stage.stage_id),
        )
        existing = cursor.fetchone()
        if existing is None or existing[0] != stage.run_id or existing[1] != immutable_checksum:
            raise IdempotencyConflict(
                f"stage {stage.project_id}/{stage.stage_id} was replayed differently"
            )
        p = self.placeholder
        cursor.execute(
            f"UPDATE {self._table('run_stage')} SET status = CASE "
            f"WHEN status IN ('success', 'failed', 'error', 'cancelled', 'canceled', 'skipped') "
            f"THEN status ELSE {p} END, "
            f"finished_at = CASE WHEN status IN "
            f"('success', 'failed', 'error', 'cancelled', 'canceled', 'skipped') "
            f"THEN COALESCE(finished_at, {p}) ELSE COALESCE({p}, finished_at) END, "
            f"metrics = CASE WHEN status IN "
            f"('success', 'failed', 'error', 'cancelled', 'canceled', 'skipped') "
            f"THEN metrics ELSE {p} END, error = CASE WHEN status IN "
            f"('success', 'failed', 'error', 'cancelled', 'canceled', 'skipped') "
            f"THEN COALESCE(error, {p}) ELSE COALESCE({p}, error) END "
            f"WHERE project_id = {p} AND run_id = {p} AND stage_id = {p}",
            (
                stage.status,
                _timestamp(stage.finished_at),
                _timestamp(stage.finished_at),
                _json(stage.metrics),
                _text(stage.error),
                _text(stage.error),
                stage.project_id,
                stage.run_id,
                stage.stage_id,
            ),
        )

    def _insert_resource(self, cursor: Any, resource: RunResource) -> None:
        self._require_id("resource_id", resource.resource_id)
        record_checksum = payload_checksum(
            {key: value for key, value in asdict(resource).items() if key != "resource_id"}
        )
        values = (
            resource.resource_id,
            resource.project_id,
            resource.run_id,
            resource.resource_kind,
            resource.role,
            _text(resource.normalized_identity),
            _text(resource.uri),
            _text(resource.table_name),
            _text(resource.catalog),
            _text(resource.ref_name),
            _text(resource.schema_hash),
            _text(resource.watermark),
            resource.record_count,
            resource.byte_count,
            _json(resource.staged_objects),
            _text(resource.snapshot_before),
            _text(resource.snapshot_after),
            record_checksum,
        )
        cursor.execute(
            f"INSERT INTO {self._table('run_resource')} "
            "(resource_id, project_id, run_id, resource_kind, role, normalized_identity, uri, "
            "table_name, catalog, ref_name, schema_hash, watermark, record_count, byte_count, "
            "staged_objects, snapshot_before, snapshot_after, record_checksum) VALUES ("
            + ", ".join([self.placeholder] * len(values))
            + ") ON CONFLICT (project_id, run_id, resource_id) DO NOTHING",
            values,
        )
        if cursor.rowcount != 1:
            self._confirm_immutable(
                cursor,
                table="run_resource",
                id_column="resource_id",
                project_id=resource.project_id,
                record_id=resource.resource_id,
                run_id=resource.run_id,
                checksum=record_checksum,
            )

    def _insert_lineage(self, cursor: Any, edge: RunLineageEdge) -> None:
        self._require_id("lineage_edge_id", edge.lineage_edge_id)
        record_checksum = payload_checksum(
            {key: value for key, value in asdict(edge).items() if key != "lineage_edge_id"}
        )
        values = (
            edge.lineage_edge_id,
            edge.project_id,
            edge.run_id,
            _text(edge.source),
            _text(edge.target),
            _json(edge.column_mapping),
            _text(edge.origin),
            _text(edge.derivation),
            edge.confidence,
            record_checksum,
        )
        cursor.execute(
            f"INSERT INTO {self._table('run_lineage_edge')} "
            "(lineage_edge_id, project_id, run_id, source, target, column_mapping, origin, "
            "derivation, confidence, record_checksum) VALUES ("
            + ", ".join([self.placeholder] * len(values))
            + ") ON CONFLICT (project_id, run_id, lineage_edge_id) DO NOTHING",
            values,
        )
        if cursor.rowcount != 1:
            self._confirm_immutable(
                cursor,
                table="run_lineage_edge",
                id_column="lineage_edge_id",
                project_id=edge.project_id,
                record_id=edge.lineage_edge_id,
                run_id=edge.run_id,
                checksum=record_checksum,
            )

    def _insert_quality(self, cursor: Any, result: RunQualityResult) -> None:
        self._require_id("quality_result_id", result.quality_result_id)
        record_checksum = payload_checksum(
            {key: value for key, value in asdict(result).items() if key != "quality_result_id"}
        )
        values = (
            result.quality_result_id,
            result.project_id,
            result.run_id,
            result.stage_id,
            _text(result.check_id),
            _text(result.asset),
            _text(result.severity),
            result.blocking,
            result.passed,
            result.evaluated_count,
            result.failed_count,
            _text(result.failure_artifact_id),
            _json(result.metadata),
            record_checksum,
        )
        cursor.execute(
            f"INSERT INTO {self._table('run_quality_result')} "
            "(quality_result_id, project_id, run_id, stage_id, check_id, asset, severity, blocking, "
            "passed, evaluated_count, failed_count, failure_artifact_id, metadata, record_checksum) VALUES ("
            + ", ".join([self.placeholder] * len(values))
            + ") ON CONFLICT (project_id, run_id, quality_result_id) DO NOTHING",
            values,
        )
        if cursor.rowcount != 1:
            self._confirm_immutable(
                cursor,
                table="run_quality_result",
                id_column="quality_result_id",
                project_id=result.project_id,
                record_id=result.quality_result_id,
                run_id=result.run_id,
                checksum=record_checksum,
            )

    def _insert_catalog_change(self, cursor: Any, change: RunCatalogChange) -> None:
        self._require_id("catalog_change_id", change.catalog_change_id)
        record_checksum = payload_checksum(
            {key: value for key, value in asdict(change).items() if key != "catalog_change_id"}
        )
        values = (
            change.catalog_change_id,
            change.project_id,
            change.run_id,
            _text(change.catalog_ref),
            _text(change.content_key),
            _text(change.operation),
            _text(change.source_hash),
            _text(change.target_hash),
            _text(change.commit_hash),
            _text(change.commit_message),
            _text(change.merge_outcome),
            _text(change.snapshot_before),
            _text(change.snapshot_after),
            _json(change.metadata),
            record_checksum,
        )
        cursor.execute(
            f"INSERT INTO {self._table('run_catalog_change')} "
            "(catalog_change_id, project_id, run_id, catalog_ref, content_key, operation, "
            "source_hash, target_hash, commit_hash, commit_message, merge_outcome, snapshot_before, "
            "snapshot_after, metadata, record_checksum) VALUES ("
            + ", ".join([self.placeholder] * len(values))
            + ") ON CONFLICT (project_id, run_id, catalog_change_id) DO NOTHING",
            values,
        )
        if cursor.rowcount != 1:
            self._confirm_immutable(
                cursor,
                table="run_catalog_change",
                id_column="catalog_change_id",
                project_id=change.project_id,
                record_id=change.catalog_change_id,
                run_id=change.run_id,
                checksum=record_checksum,
            )

    def _insert_artifact(self, cursor: Any, artifact: RunArtifact) -> None:
        self._require_id("artifact_id", artifact.artifact_id)
        record_checksum = payload_checksum(
            {key: value for key, value in asdict(artifact).items() if key != "artifact_id"}
        )
        values = (
            artifact.artifact_id,
            artifact.project_id,
            artifact.run_id,
            _text(artifact.artifact_kind),
            _text(artifact.uri),
            _text(artifact.content_type),
            _text(artifact.checksum),
            _text(artifact.retention_class),
            _timestamp(artifact.expires_at),
            artifact.legal_hold,
            artifact.status.value,
            record_checksum,
        )
        cursor.execute(
            f"INSERT INTO {self._table('run_artifact')} "
            "(artifact_id, project_id, run_id, artifact_kind, uri, content_type, checksum, "
            "retention_class, expires_at, legal_hold, status, record_checksum) VALUES ("
            + ", ".join([self.placeholder] * len(values))
            + ") ON CONFLICT (project_id, run_id, artifact_id) DO NOTHING",
            values,
        )
        if cursor.rowcount != 1:
            self._confirm_immutable(
                cursor,
                table="run_artifact",
                id_column="artifact_id",
                project_id=artifact.project_id,
                record_id=artifact.artifact_id,
                run_id=artifact.run_id,
                checksum=record_checksum,
            )

    @staticmethod
    def _row_dict(cursor: Any, row: Any) -> dict[str, Any]:
        if hasattr(row, "keys"):
            return dict(row)
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, row, strict=True))

    @staticmethod
    def _require_id(name: str, value: str) -> None:
        if not value or not value.strip():
            raise ValueError(f"{name} must be a stable non-empty identifier")

    def _confirm_immutable(
        self,
        cursor: Any,
        *,
        table: str,
        id_column: str,
        project_id: str,
        record_id: str,
        run_id: str,
        checksum: str,
    ) -> None:
        cursor.execute(
            f"SELECT run_id, record_checksum FROM {self._table(table)} "
            f"WHERE project_id = {self.placeholder} AND run_id = {self.placeholder} "
            f"AND {id_column} = {self.placeholder}",
            (project_id, run_id, record_id),
        )
        existing = cursor.fetchone()
        if existing is None or existing[0] != run_id or existing[1] != checksum:
            raise IdempotencyConflict(
                f"{table} {project_id}/{record_id} was replayed with different evidence"
            )


class SQLiteRunEvidenceStore(_SqlRunEvidenceStore):
    """Local SQLite fallback for single-process development and tests."""

    placeholder = "?"

    def __init__(self, path: str | Path = ":memory:") -> None:
        super().__init__()
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA busy_timeout = 5000")
        if self.path != ":memory:":
            self._connection.execute("PRAGMA journal_mode = WAL")

    def _connect(self) -> sqlite3.Connection:
        return self._connection

    def _close_connection(self, connection: sqlite3.Connection) -> None:
        del connection

    def _initialize_schema(self) -> None:
        sql_path = Path(__file__).parent.parent / "sql" / "002_create_run_evidence.sql"
        sql = sql_path.read_text(encoding="utf-8")
        replacements = {
            "CREATE SCHEMA IF NOT EXISTS phlo;": "",
            "phlo.": "",
            "BIGSERIAL": "INTEGER",
            "TIMESTAMPTZ": "TEXT",
            "JSONB": "TEXT",
            "DOUBLE PRECISION": "REAL",
            "BOOLEAN": "INTEGER",
            "DEFAULT NOW()": "DEFAULT CURRENT_TIMESTAMP",
            "DEFAULT '{}'::jsonb": "DEFAULT '{}'",
            "DEFAULT '[]'::jsonb": "DEFAULT '[]'",
            "INSERT INTO run_evidence_schema_version(version) VALUES (1)\nON CONFLICT (version) DO NOTHING;": "INSERT OR IGNORE INTO run_evidence_schema_version(version) VALUES (1);",
        }
        for old, new in replacements.items():
            sql = sql.replace(old, new)
        sql = "\n".join(
            line for line in sql.splitlines() if not line.strip().startswith("COMMENT ON")
        )
        self._connection.executescript(sql)
        self._connection.commit()


class PostgresRunEvidenceStore(_SqlRunEvidenceStore):
    """Production PostgreSQL adapter using the runtime psycopg2 dependency."""

    placeholder = "%s"
    table_prefix = "phlo."

    def __init__(self, dsn: str, *, connection_factory: Any | None = None) -> None:
        super().__init__()
        self.dsn = dsn
        self._connection_factory = connection_factory

    def _connect(self) -> Any:
        if self._connection_factory is not None:
            return self._connection_factory()
        try:
            import psycopg2
        except ImportError as exc:
            raise RuntimeError(
                "PostgresRunEvidenceStore requires the runtime extra: install phlo[runtime]."
            ) from exc
        return psycopg2.connect(self.dsn)

    def _initialize_schema(self) -> None:
        sql_path = Path(__file__).parent.parent / "sql" / "002_create_run_evidence.sql"
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql_path.read_text(encoding="utf-8"))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


def default_run_evidence_store() -> SQLiteRunEvidenceStore | PostgresRunEvidenceStore:
    """Resolve the production DSN or durable local path from environment."""
    dsn = os.environ.get("PHLO_RUN_EVIDENCE_DB_URL")
    if dsn:
        return PostgresRunEvidenceStore(dsn)
    environment = os.environ.get("PHLO_ENVIRONMENT", "dev").lower()
    if environment in {"prod", "production", "staging", "regulated"}:
        raise RuntimeError(
            "Run evidence requires PHLO_RUN_EVIDENCE_DB_URL in production, staging, "
            "and regulated environments; SQLite is local-only."
        )
    path = os.environ.get("PHLO_RUN_EVIDENCE_SQLITE_PATH", ".phlo/run-evidence.sqlite")
    return SQLiteRunEvidenceStore(path)
