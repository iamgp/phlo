"""Tests for the Polaris snapshot promotion state machine."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from phlo_polaris.promotion import (
    CANDIDATE_REF_PREFIX,
    PolarisSnapshotPromotionCatalog,
    ReleaseConflictError,
    candidate_ref_for_run,
    run_id_from_namespace,
)


class FakeStore:
    """In-memory ledger standing in for the Iceberg release store."""

    def __init__(self) -> None:
        self._rows: list[dict] = []
        self.appended: list[list[dict]] = []

    def rows(self) -> list[dict]:
        return list(self._rows)

    def append(self, rows: list[dict]) -> None:
        self.appended.append(rows)
        self._rows.extend(rows)

    def current_revision(self) -> int:
        return max(
            (int(r["revision"]) for r in self._rows if r.get("kind") == "state"),
            default=0,
        )


class FakeTable:
    """Fake Iceberg table with snapshot-reference management."""

    def __init__(self, snapshot_id: int = 11) -> None:
        self.snapshot_id = snapshot_id
        self.refs: dict[str, int] = {}
        self.dropped: list[str] = []

    def current_snapshot_id(self) -> int:
        return self.snapshot_id

    def manage_snapshots(self) -> "FakeSnapshotManager":
        return FakeSnapshotManager(self)


class FakeSnapshotManager:
    def __init__(self, table: FakeTable) -> None:
        self._table = table
        self._operations: list[tuple] = []

    def create_branch(self, ref: str, snapshot_id: int) -> "FakeSnapshotManager":
        self._operations.append(("create", ref, snapshot_id))
        return self

    def drop_branch(self, ref: str) -> "FakeSnapshotManager":
        self._operations.append(("drop", ref))
        return self

    def commit(self) -> None:
        for operation in self._operations:
            if operation[0] == "create":
                self._table.refs[operation[1]] = operation[2]
            else:
                self._table.refs.pop(operation[1], None)
                self._table.dropped.append(operation[1])
        self._operations = []


def _catalog() -> tuple[PolarisSnapshotPromotionCatalog, FakeStore, dict]:
    store = FakeStore()
    tables = {"bronze.events": FakeTable(11), "bronze.orders": FakeTable(22)}
    catalog = PolarisSnapshotPromotionCatalog(store=store, table_opener=lambda name: tables[name])
    return catalog, store, tables


def test_candidate_ref_is_deterministic_and_reversible() -> None:
    assert candidate_ref_for_run("abc") == f"{CANDIDATE_REF_PREFIX}abc"
    assert run_id_from_namespace("pipeline-run-abc") == "abc"
    assert run_id_from_namespace("phlo_candidates__abc") == "abc"


def test_create_candidate_opens_snapshot_ref_and_records_ledger_row() -> None:
    catalog, store, tables = _catalog()
    candidate = catalog.create_candidate(table_name="bronze.events", run_id="run-1")
    assert candidate.snapshot_id == 11
    assert candidate.namespace == "pipeline-run-run-1"
    assert tables["bronze.events"].refs == {CANDIDATE_REF_PREFIX + "run-1": 11}
    assert store.rows()[0]["kind"] == "candidate"
    assert store.rows()[0]["status"] == "open"


def test_promote_advances_pointer_with_atomic_ledger_commit() -> None:
    catalog, store, _ = _catalog()
    catalog.create_candidate(table_name="bronze.events", run_id="run-1")
    catalog.create_candidate(table_name="bronze.orders", run_id="run-1")

    records = catalog.promote_candidates(
        namespace="pipeline-run-run-1", release_id="release-1", expected_revision=0
    )

    assert {record.table_name for record in records} == {"bronze.events", "bronze.orders"}
    assert all(record.revision == 1 for record in records)
    # One atomic append carries the release rows and the new pointer state.
    assert len(store.appended[-1]) == 3
    assert catalog.release_revision() == 1


def test_promote_refuses_stale_expected_revision() -> None:
    catalog, _, _ = _catalog()
    catalog.create_candidate(table_name="bronze.events", run_id="run-1")
    catalog.promote_candidates(namespace="pipeline-run-run-1", release_id="r1")

    with pytest.raises(ReleaseConflictError, match="Release pointer moved"):
        catalog.promote_candidates(
            namespace="pipeline-run-run-1",
            release_id="r2",
            expected_revision=0,
        )


def test_resolve_release_returns_latest_revision_record() -> None:
    catalog, _, _ = _catalog()
    catalog.create_candidate(table_name="bronze.events", run_id="run-1")
    catalog.promote_candidates(namespace="pipeline-run-run-1", release_id="r1")
    catalog.create_candidate(table_name="bronze.events", run_id="run-2")
    catalog.promote_candidates(namespace="pipeline-run-run-2", release_id="r2")

    release = catalog.resolve_release(table_name="bronze.events")
    assert release is not None
    assert release.release_id == "r2"
    assert release.revision == 2


def test_promote_without_candidates_returns_empty() -> None:
    catalog, _, _ = _catalog()
    assert catalog.promote_candidates(namespace="pipeline-run-none", release_id="r1") == []


def test_abort_candidates_drops_refs_and_marks_ledger() -> None:
    catalog, store, tables = _catalog()
    catalog.create_candidate(table_name="bronze.events", run_id="run-1")

    assert catalog.abort_candidates(namespace="pipeline-run-run-1") is True
    assert tables["bronze.events"].refs == {}
    statuses = [row["status"] for row in store.rows() if row["kind"] == "candidate"]
    assert statuses.count("aborted") == 1
    assert catalog.list_candidates(namespace="pipeline-run-run-1") == []


def test_abort_is_idempotent_when_nothing_is_open() -> None:
    catalog, _, _ = _catalog()
    assert catalog.abort_candidates(namespace="pipeline-run-empty") is True


def test_prune_candidates_drops_only_expired_refs() -> None:
    catalog, store, tables = _catalog()
    catalog.create_candidate(table_name="bronze.events", run_id="old")
    for row in store.rows():
        if row.get("run_id") == "old":
            row["recorded_at"] = datetime.now(timezone.utc) - timedelta(hours=48)
    catalog.create_candidate(table_name="bronze.orders", run_id="new")

    pruned = catalog.prune_candidates(older_than=datetime.now(timezone.utc) - timedelta(hours=24))

    assert pruned == ["pipeline-run-old"]
    assert tables["bronze.events"].refs == {}
    assert tables["bronze.orders"].refs != {}
