"""Focused tests for the versioned run-evidence contract and sink."""

from __future__ import annotations

import sqlite3
from dataclasses import replace

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
            "SELECT COUNT(*) FROM run_stage WHERE project_id = ? AND run_id = ?", ("project", "run")
        )
        assert cursor.fetchone()[0] == 2


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
