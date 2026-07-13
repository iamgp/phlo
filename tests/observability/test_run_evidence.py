"""Focused tests for the versioned run-evidence contract and sink."""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from phlo.hooks.emitters import (
    IngestionEventContext,
    IngestionEventEmitter,
    LineageEventContext,
    LineageEventEmitter,
    QualityResultEventContext,
    QualityResultEventEmitter,
)
from phlo.hooks.events import (
    HookCorrelation,
    IngestionEvent,
    LineageEvent,
    PublishEvent,
    QualityResultEvent,
    TransformEvent,
)
from phlo.run_evidence import (
    RUN_EVIDENCE_SCHEMA_VERSION,
    EvidenceCompleteness,
    IdempotencyConflict,
    PipelineRun,
    RunArtifact,
    RunCatalogChange,
    RunEvent,
    RunLineageEdge,
    RunQualityResult,
    RunResource,
    RunStage,
    SQLiteRunEvidenceStore,
    default_run_evidence_store,
)
from phlo.run_evidence.hooks import CoreRunEvidenceHookProvider


def _store_with_run(*, project_id: str = "project", run_id: str = "run") -> SQLiteRunEvidenceStore:
    store = SQLiteRunEvidenceStore(":memory:")
    store.append_pipeline_run(PipelineRun(project_id=project_id, run_id=run_id))
    return store


def _event(*, payload: dict, event_id: str = "event", producer: str = "producer") -> RunEvent:
    return RunEvent(
        project_id="project",
        run_id="run",
        event_id=event_id,
        event_type="ingestion.start",
        producer=producer,
        payload=payload,
    )


def test_event_append_is_redacted_checksumed_and_idempotent() -> None:
    store = _store_with_run()
    event = _event(payload={"nested": {"token": "secret", "value": 1}})

    assert store.append_event(event) is True
    replay = replace(event, payload={"nested": {"value": 1, "token": "another-secret"}})
    assert store.append_event(replay) is False

    row = store.list_events("project", "run")[0]
    assert "secret" not in row["payload"]
    assert "<redacted>" in row["payload"]
    assert row["schema_version"] == "1.0"


def test_event_identity_is_scoped_by_project_and_producer() -> None:
    store = SQLiteRunEvidenceStore(":memory:")
    store.append_pipeline_run(PipelineRun(project_id="one", run_id="same"))
    store.append_pipeline_run(PipelineRun(project_id="two", run_id="same"))
    first = replace(_event(payload={"value": 1}), project_id="one", run_id="same")

    assert store.append_event(first, run=PipelineRun(project_id="one", run_id="same")) is True
    assert (
        store.append_event(
            replace(first, project_id="two", run_id="same"),
            run=PipelineRun(project_id="two", run_id="same"),
        )
        is True
    )
    assert store.append_event(replace(first, producer="other")) is True


def test_event_payload_conflict_rolls_back_and_preserves_original() -> None:
    store = _store_with_run()
    event = _event(payload={"value": 1})
    store.append_event(event)

    with pytest.raises(IdempotencyConflict):
        store.append_event(replace(event, payload={"value": 2}))

    assert store.list_events("project", "run")[0]["payload"] == '{"value":1}'


def test_event_and_derived_rows_share_one_transaction(monkeypatch: pytest.MonkeyPatch) -> None:
    store = _store_with_run()
    stage = RunStage(project_id="project", run_id="run", stage_id="stage", stage_type="ingest")

    def fail_after_event(*_args, **_kwargs) -> None:
        raise RuntimeError("failpoint")

    monkeypatch.setattr(store, "_insert_stage", fail_after_event)
    with pytest.raises(RuntimeError, match="failpoint"):
        store.append_event(_event(payload={"value": 1}), stage=stage)

    assert store.count_events("project", "run") == 0
    monkeypatch.setattr(store, "_insert_stage", SQLiteRunEvidenceStore._insert_stage.__get__(store))
    assert store.append_event(_event(payload={"value": 1}), stage=stage) is True


@pytest.mark.parametrize(
    ("family", "first", "different"),
    [
        (
            "stage",
            RunStage(project_id="project", run_id="run", stage_id="stable", stage_type="ingest"),
            RunStage(project_id="project", run_id="run", stage_id="stable", stage_type="transform"),
        ),
        (
            "resource",
            RunResource(project_id="project", run_id="run", resource_id="stable", uri="a"),
            RunResource(project_id="project", run_id="run", resource_id="stable", uri="b"),
        ),
        (
            "lineage",
            RunLineageEdge(
                project_id="project", run_id="run", lineage_edge_id="stable", source="a", target="b"
            ),
            RunLineageEdge(
                project_id="project", run_id="run", lineage_edge_id="stable", source="a", target="c"
            ),
        ),
        (
            "quality",
            RunQualityResult(
                project_id="project",
                run_id="run",
                quality_result_id="stable",
                check_id="check",
                passed=True,
            ),
            RunQualityResult(
                project_id="project",
                run_id="run",
                quality_result_id="stable",
                check_id="other",
                passed=True,
            ),
        ),
        (
            "catalog",
            RunCatalogChange(
                project_id="project", run_id="run", catalog_change_id="stable", operation="commit"
            ),
            RunCatalogChange(
                project_id="project", run_id="run", catalog_change_id="stable", operation="merge"
            ),
        ),
        (
            "artifact",
            RunArtifact(
                project_id="project", run_id="run", artifact_id="stable", artifact_kind="log"
            ),
            RunArtifact(
                project_id="project", run_id="run", artifact_id="stable", artifact_kind="manifest"
            ),
        ),
    ],
)
def test_normalized_records_are_idempotent_and_conflict_on_content(
    family, first, different
) -> None:
    store = _store_with_run()
    append = getattr(
        store,
        f"append_{'lineage_edge' if family == 'lineage' else 'quality_result' if family == 'quality' else 'catalog_change' if family == 'catalog' else family}",
    )

    append(first)
    append(first)
    with pytest.raises(IdempotencyConflict):
        append(different)


def test_child_ids_are_project_scoped_and_cross_run_quality_refs_fail() -> None:
    store = SQLiteRunEvidenceStore(":memory:")
    store.append_pipeline_run(PipelineRun(project_id="project", run_id="one"))
    store.append_pipeline_run(PipelineRun(project_id="project", run_id="two"))
    store.append_pipeline_run(PipelineRun(project_id="other", run_id="one"))
    store.append_stage(
        RunStage(project_id="project", run_id="one", stage_id="same", stage_type="ingest")
    )
    store.append_stage(
        RunStage(project_id="other", run_id="one", stage_id="same", stage_type="ingest")
    )

    with pytest.raises(sqlite3.IntegrityError):
        store.append_quality_result(
            RunQualityResult(
                project_id="project",
                run_id="two",
                quality_result_id="quality",
                check_id="check",
                stage_id="same",
            )
        )
    store.append_artifact(
        RunArtifact(project_id="project", run_id="one", artifact_id="artifact", artifact_kind="log")
    )
    with pytest.raises(sqlite3.IntegrityError):
        store.append_quality_result(
            RunQualityResult(
                project_id="project",
                run_id="two",
                quality_result_id="quality-artifact",
                check_id="check",
                failure_artifact_id="artifact",
            )
        )


def test_same_project_child_ids_are_scoped_to_each_run() -> None:
    store = SQLiteRunEvidenceStore(":memory:")
    for run_id in ("one", "two"):
        store.append_pipeline_run(PipelineRun(project_id="project", run_id=run_id))

    store.append_stage(
        RunStage(project_id="project", run_id="one", stage_id="same", stage_type="ingest")
    )
    store.append_stage(
        RunStage(project_id="project", run_id="two", stage_id="same", stage_type="ingest")
    )
    store.append_resource(
        RunResource(project_id="project", run_id="one", resource_id="same", uri="one")
    )
    store.append_resource(
        RunResource(project_id="project", run_id="two", resource_id="same", uri="two")
    )
    store.append_lineage_edge(
        RunLineageEdge(
            project_id="project", run_id="one", lineage_edge_id="same", source="a", target="b"
        )
    )
    store.append_lineage_edge(
        RunLineageEdge(
            project_id="project", run_id="two", lineage_edge_id="same", source="a", target="c"
        )
    )
    store.append_quality_result(
        RunQualityResult(
            project_id="project", run_id="one", quality_result_id="same", check_id="one"
        )
    )
    store.append_quality_result(
        RunQualityResult(
            project_id="project", run_id="two", quality_result_id="same", check_id="two"
        )
    )
    store.append_catalog_change(
        RunCatalogChange(
            project_id="project", run_id="one", catalog_change_id="same", operation="commit"
        )
    )
    store.append_catalog_change(
        RunCatalogChange(
            project_id="project", run_id="two", catalog_change_id="same", operation="merge"
        )
    )
    store.append_artifact(
        RunArtifact(project_id="project", run_id="one", artifact_id="same", artifact_kind="log")
    )
    store.append_artifact(
        RunArtifact(
            project_id="project", run_id="two", artifact_id="same", artifact_kind="manifest"
        )
    )

    with store._transaction() as (_, cursor):
        for table in (
            "run_stage",
            "run_resource",
            "run_lineage_edge",
            "run_quality_result",
            "run_catalog_change",
            "run_artifact",
        ):
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE project_id = ?", ("project",))
            assert cursor.fetchone()[0] == 2, table


def test_child_primary_keys_include_project_and_run() -> None:
    store = SQLiteRunEvidenceStore(":memory:")
    expected = {
        "run_stage": ["project_id", "run_id", "stage_id"],
        "run_resource": ["project_id", "run_id", "resource_id"],
        "run_lineage_edge": ["project_id", "run_id", "lineage_edge_id"],
        "run_quality_result": ["project_id", "run_id", "quality_result_id"],
        "run_catalog_change": ["project_id", "run_id", "catalog_change_id"],
        "run_artifact": ["project_id", "run_id", "artifact_id"],
    }
    with store._transaction() as (_, cursor):
        for table, columns in expected.items():
            cursor.execute(f"PRAGMA table_info({table})")
            primary_key = [
                row[1] for row in sorted(cursor.fetchall(), key=lambda row: row[5]) if row[5]
            ]
            assert primary_key == columns, table


def test_run_attempt_and_terminal_status_are_monotonic() -> None:
    store = SQLiteRunEvidenceStore(":memory:")
    store.append_pipeline_run(
        PipelineRun(project_id="project", run_id="run", attempt=1, status="failed")
    )
    store.append_pipeline_run(
        PipelineRun(project_id="project", run_id="run", attempt=2, status="running")
    )
    store.append_pipeline_run(
        PipelineRun(project_id="project", run_id="run", attempt=2, status="success")
    )

    row = store.get_run("project", "run")
    assert row["attempt"] == 2
    assert row["status"] == "success"

    store.append_pipeline_run(
        PipelineRun(project_id="project", run_id="run", attempt=1, status="failed")
    )
    store.append_pipeline_run(
        PipelineRun(project_id="project", run_id="run", attempt=2, status="failed")
    )

    row = store.get_run("project", "run")
    assert row["attempt"] == 2
    assert row["status"] == "success"


def test_higher_attempt_replaces_summary_and_late_attempt_is_ignored() -> None:
    store = SQLiteRunEvidenceStore(":memory:")
    first_finished = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
    second_finished = datetime(2026, 7, 13, 12, 1, tzinfo=UTC)
    late_first_finished = datetime(2026, 7, 13, 12, 2, tzinfo=UTC)
    first = PipelineRun(
        project_id="project",
        run_id="run",
        attempt=1,
        trace_id="trace-one",
        effective_identity="identity-one",
        code_version="code-one",
        config_version="config-one",
        status="failed",
        finished_at=first_finished,
        failure_summary="first failure",
        evidence_completeness=EvidenceCompleteness.COMPLETE,
    )
    second_running = replace(
        first,
        attempt=2,
        trace_id="trace-two",
        effective_identity="identity-two",
        code_version="code-two",
        config_version="config-two",
        status="running",
        finished_at=None,
        failure_summary=None,
        evidence_completeness=EvidenceCompleteness.INCOMPLETE,
    )
    store.append_pipeline_run(first)
    store.append_pipeline_run(second_running)

    row = store.get_run("project", "run")
    assert (
        row["attempt"],
        row["status"],
        row["trace_id"],
        row["effective_identity"],
        row["code_version"],
        row["config_version"],
    ) == (2, "running", "trace-two", "identity-two", "code-two", "config-two")
    assert row["finished_at"] is None
    assert row["failure_summary"] is None
    assert row["evidence_completeness"] == EvidenceCompleteness.INCOMPLETE

    store.append_pipeline_run(
        replace(
            second_running,
            status="success",
            finished_at=second_finished,
            evidence_completeness=EvidenceCompleteness.COMPLETE,
        )
    )
    store.append_pipeline_run(
        replace(
            first,
            trace_id="late-trace-one",
            effective_identity="late-identity-one",
            code_version="late-code-one",
            config_version="late-config-one",
            finished_at=late_first_finished,
            failure_summary="late first failure",
            evidence_completeness=EvidenceCompleteness.REDACTED,
        )
    )

    row = store.get_run("project", "run")
    assert (
        row["attempt"],
        row["status"],
        row["trace_id"],
        row["effective_identity"],
        row["code_version"],
        row["config_version"],
    ) == (2, "success", "trace-two", "identity-two", "code-two", "config-two")
    assert row["finished_at"] == second_finished.isoformat()
    assert row["failure_summary"] is None
    assert row["evidence_completeness"] == EvidenceCompleteness.COMPLETE


def test_terminal_stage_status_and_metadata_are_sticky() -> None:
    store = _store_with_run()
    first_finished = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
    later_finished = datetime(2026, 7, 13, 12, 1, tzinfo=UTC)
    first = RunStage(
        project_id="project",
        run_id="run",
        stage_id="stage",
        stage_type="ingest",
        status="failed",
        finished_at=first_finished,
        metrics={"rows": 10, "bytes": 100},
        error="first failure",
    )
    store.append_stage(first)
    store.append_stage(
        replace(
            first,
            status="success",
            finished_at=later_finished,
            metrics={"rows": 20},
            error="late outcome",
        )
    )
    store.append_stage(replace(first, status="running", finished_at=None, metrics={}, error=None))

    with store._transaction() as (_, cursor):
        cursor.execute(
            "SELECT status, finished_at, metrics, error FROM run_stage "
            "WHERE project_id = ? AND run_id = ? AND stage_id = ?",
            ("project", "run", "stage"),
        )
        row = cursor.fetchone()
    assert row[0] == "failed"
    assert row[1] == first_finished.isoformat()
    assert row[2] == '{"bytes":100,"rows":10}'
    assert row[3] == "first failure"


def test_previous_event_schema_version_remains_readable() -> None:
    store = _store_with_run()
    assert store.append_event(_event(payload={"value": 1}, event_id="old")) is True
    store.append_event(
        replace(_event(payload={"value": 2}, event_id="previous"), schema_version="0.9")
    )
    assert store.list_events("project", "run")[-1]["schema_version"] == "0.9"


def test_sqlite_migration_is_versioned_and_idempotent() -> None:
    store = SQLiteRunEvidenceStore(":memory:")
    store._initialize_schema()
    store._initialize_schema()
    with store._transaction() as (_, cursor):
        cursor.execute("SELECT version FROM run_evidence_schema_version")
        assert [row[0] for row in cursor.fetchall()] == [RUN_EVIDENCE_SCHEMA_VERSION]


def test_core_sink_records_all_correlated_lifecycle_families() -> None:
    store = SQLiteRunEvidenceStore(":memory:")
    provider = CoreRunEvidenceHookProvider(store)
    correlation = HookCorrelation(project_id="project", run_id="run", job_name="job")
    events = [
        IngestionEvent(
            event_type="ingestion.start",
            asset_key="raw",
            table_name="raw",
            group_name="raw",
            correlation=correlation,
        ),
        TransformEvent(
            event_type="transform.start", tool="dbt", asset_key="model", correlation=correlation
        ),
        QualityResultEvent(
            event_type="quality.result",
            asset_key="model",
            check_name="valid",
            passed=True,
            correlation=correlation,
        ),
        PublishEvent(
            event_type="publish.end", asset_key="model", status="success", correlation=correlation
        ),
        LineageEvent(event_type="lineage.edges", edges=[("raw", "model")], correlation=correlation),
    ]

    for event in events:
        provider._handle_event(event)

    assert store.count_events("project", "run") == 5
    assert store.get_run("project", "run")["evidence_completeness"] == "incomplete"


def test_standard_emitter_reconstructs_same_event_identity_for_retry() -> None:
    store = SQLiteRunEvidenceStore(":memory:")
    provider = CoreRunEvidenceHookProvider(store)
    context = IngestionEventContext(
        asset_key="raw",
        table_name="raw",
        group_name="raw",
        project_id="project",
        run_id="run",
    )

    first_bus = type("Bus", (), {"emit": lambda self, event: provider._handle_event(event)})()
    IngestionEventEmitter(context, hook_bus=first_bus).emit_start()
    IngestionEventEmitter(context, hook_bus=first_bus).emit_start()

    assert store.count_events("project", "run") == 1


def test_production_requires_postgres_run_evidence_store(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PHLO_ENVIRONMENT", "production")
    monkeypatch.delenv("PHLO_RUN_EVIDENCE_DB_URL", raising=False)
    monkeypatch.delenv("PHLO_RUN_EVIDENCE_SQLITE_PATH", raising=False)

    with pytest.raises(RuntimeError, match="requires PHLO_RUN_EVIDENCE_DB_URL"):
        default_run_evidence_store()


def test_incomplete_correlation_is_not_persisted() -> None:
    provider = CoreRunEvidenceHookProvider(SQLiteRunEvidenceStore(":memory:"))
    provider._handle_event(
        IngestionEvent(
            event_type="ingestion.start",
            asset_key="raw",
            table_name="raw",
            group_name="raw",
            correlation=HookCorrelation(run_id="run"),
        )
    )
    assert provider._store is not None
    assert provider._store.get_run("unknown", "run") is None


def test_quality_and_lineage_identities_include_logical_operation() -> None:
    store = SQLiteRunEvidenceStore(":memory:")
    provider = CoreRunEvidenceHookProvider(store)
    correlation = HookCorrelation(project_id="project", run_id="run", trace_id="trace-a")
    quality = QualityResultEventContext(
        asset_key="model", project_id="project", run_id="run", correlation=correlation
    )
    quality_bus = type("Bus", (), {"emit": lambda self, event: provider._handle_event(event)})()
    QualityResultEventEmitter(quality, hook_bus=quality_bus).emit_result(
        check_name="nulls", passed=True
    )
    QualityResultEventEmitter(quality, hook_bus=quality_bus).emit_result(
        check_name="uniqueness", passed=True
    )
    retry_quality = replace(correlation, trace_id="trace-b")
    QualityResultEventEmitter(
        replace(quality, correlation=retry_quality), hook_bus=quality_bus
    ).emit_result(check_name="nulls", passed=True)

    lineage = LineageEventContext(project_id="project", run_id="run", correlation=correlation)
    lineage_emitter = LineageEventEmitter(lineage, hook_bus=quality_bus)
    lineage_emitter.emit_edges(edges=[("a", "b")], operation_id="batch-1")
    lineage_emitter.emit_edges(edges=[("a", "b")], operation_id="batch-2")

    assert store.count_events("project", "run") == 4
    assert store.get_run("project", "run")["trace_id"] == "trace-a"


def test_correlated_lineage_requires_explicit_operation_identity() -> None:
    emitter = LineageEventEmitter(
        LineageEventContext(
            project_id="project",
            run_id="run",
            correlation=HookCorrelation(project_id="project", run_id="run"),
        ),
        hook_bus=type("Bus", (), {"emit": lambda self, event: None})(),
    )
    with pytest.raises(ValueError, match="operation_id or event_id"):
        emitter.emit_edges(edges=[("a", "b")])


def test_retry_attempts_get_distinct_stage_evidence() -> None:
    store = SQLiteRunEvidenceStore(":memory:")
    provider = CoreRunEvidenceHookProvider(store)
    for attempt in (1, 2):
        provider._handle_event(
            IngestionEvent(
                event_type="ingestion.end",
                asset_key="raw",
                table_name="raw",
                group_name="raw",
                status="failed" if attempt == 1 else "success",
                correlation=HookCorrelation(project_id="project", run_id="run", attempt=attempt),
            )
        )

    with store._transaction() as (_, cursor):
        cursor.execute(
            "SELECT attempt FROM run_stage WHERE project_id = ? AND run_id = ? ORDER BY attempt",
            ("project", "run"),
        )
        assert [row[0] for row in cursor.fetchall()] == [1, 2]


def test_normalized_resource_payload_is_redacted() -> None:
    store = _store_with_run()
    store.append_resource(
        RunResource(
            project_id="project",
            run_id="run",
            resource_id="resource",
            uri="postgresql://user:secret@example.test/db",
            staged_objects=["s3://access_token=secret/object"],
        )
    )
    with store._transaction() as (_, cursor):
        cursor.execute(
            "SELECT uri, staged_objects FROM run_resource WHERE resource_id = ?", ("resource",)
        )
        uri, staged_objects = cursor.fetchone()
    assert "secret" not in uri
    assert "secret" not in staged_objects
