"""Focused contract tests for snapshot planning and orphan discovery."""

from typing import Any

import pytest

from phlo_iceberg.resource import (
    SAFE_MIN_RETENTION_HOURS,
    IcebergResource,
    _maintenance_plan_token,
)


def _plan(
    operation: str = "expire_snapshots", candidates: list[int] | None = None
) -> dict[str, Any]:
    candidates = candidates or []
    result: dict[str, Any] = {
        "operation": operation,
        "table_name": "raw.events",
        "ref": "main",
        "catalog": "iceberg",
        "retention_hours": SAFE_MIN_RETENTION_HOURS,
        "retention_threshold": "7d",
        "minimum_safe_retention_hours": SAFE_MIN_RETENTION_HOURS,
        "retain_last": 5,
        "before_snapshot_id": 41,
        "snapshot_count": 8,
        "candidate_snapshots": [
            {"snapshot_id": snapshot_id, "timestamp_ms": snapshot_id, "age_seconds": 1000}
            for snapshot_id in candidates
        ],
        "candidate_files": [],
        "protected_snapshot_ids": [41],
        "table_snapshot_refs": {},
        "table_snapshot_ref_evidence": "available",
        "nessie_ref_evidence": "unavailable",
        "scan_status": "available",
        "affected_objects": len(candidates),
        "affected_bytes": 100 if candidates else 0,
        "max_affected_objects": 10,
        "max_affected_bytes": 1000,
        "unavailable_fields": [],
        "trino_boundary": "pending",
        "observed_at_ms": 1,
    }
    result["plan_token"] = _maintenance_plan_token(result)
    return result


def test_dry_run_is_provider_free_and_reports_snapshot_age(monkeypatch) -> None:
    resource = IcebergResource(ref="main")
    plan = _plan(candidates=[39])
    monkeypatch.setattr(resource, "_retention_metadata", lambda **_: (plan, object()))

    result = resource.expire_snapshots(table_name="raw.events", catalog="iceberg", dry_run=True)

    assert result["status"] == "planned"
    assert result["executed"] is False
    assert result["planned"]["candidate_snapshots"][0]["snapshot_id"] == 39
    assert result["planned"]["trino_boundary"] == "not_invoked"


def test_execute_requires_exact_token_and_finite_limits(monkeypatch) -> None:
    resource = IcebergResource(ref="main")
    plan = _plan(candidates=[39])
    monkeypatch.setattr(resource, "_retention_metadata", lambda **_: (plan, object()))

    result = resource.expire_snapshots(
        table_name="raw.events",
        catalog="iceberg",
        dry_run=False,
        expected_snapshot_id=41,
        confirmation_token="tampered",
        max_affected_objects=10,
        max_affected_bytes=1000,
    )

    assert result["failure"]["code"] == "plan_token_invalid"


def test_execute_rejects_affected_object_limit_with_current_token(monkeypatch) -> None:
    resource = IcebergResource(ref="main")
    plan = _plan(candidates=[39])
    monkeypatch.setattr(resource, "_retention_metadata", lambda **_: (plan, object()))

    result = resource.expire_snapshots(
        table_name="raw.events",
        catalog="iceberg",
        dry_run=False,
        expected_snapshot_id=41,
        confirmation_token=plan["plan_token"],
        max_affected_objects=0,
        max_affected_bytes=1000,
    )

    assert result["failure"]["code"] == "affected_object_limit_exceeded"


def test_snapshot_execute_blocks_when_provider_surface_exceeds_plan(monkeypatch) -> None:
    resource = IcebergResource(ref="main")
    plan = _plan(candidates=[39])
    plan["limits_scope"] = "snapshot_count_and_data_bytes_only"
    plan["plan_token"] = _maintenance_plan_token(plan)
    monkeypatch.setattr(resource, "_retention_metadata", lambda **_: (plan, object()))

    result = resource.expire_snapshots(
        table_name="raw.events",
        catalog="iceberg",
        dry_run=False,
        expected_snapshot_id=41,
        confirmation_token=plan["plan_token"],
        max_affected_objects=1,
        max_affected_bytes=100,
    )

    assert result["status"] == "blocked"
    assert result["failure"]["code"] == "bounded_execution_unsupported"
    assert result["failure"]["retryable"] is False
    assert result["retry_safe"] is False
    assert result["planned"]["trino_boundary"] == "not_invoked"


def test_retention_floor_cannot_be_weakened() -> None:
    result = IcebergResource().cleanup_orphan_files(
        table_name="raw.events", retention_hours=1, dry_run=False
    )

    assert result["failure"]["code"] == "retention_floor_violation"
    assert result["planned"]["minimum_safe_retention_hours"] == SAFE_MIN_RETENTION_HOURS


def test_zero_candidates_is_a_noop_and_still_has_a_plan_token(monkeypatch) -> None:
    resource = IcebergResource(ref="main")
    plan = _plan()
    monkeypatch.setattr(resource, "_retention_metadata", lambda **_: (plan, object()))

    result = resource.expire_snapshots(table_name="raw.events", catalog="iceberg", dry_run=True)

    assert result["status"] == "noop"
    assert result["plan_token"] == plan["plan_token"]


def test_orphan_plan_reports_partial_age_or_size_evidence(monkeypatch) -> None:
    resource = IcebergResource(ref="main")
    plan = _plan("cleanup_orphan_files")
    plan["candidate_files"] = [{"path": "s3://lake/warehouse/raw/events/data/orphan.parquet"}]
    plan["affected_objects"] = 1
    plan["affected_bytes"] = None
    plan["unavailable_fields"] = ["candidate_age", "affected_bytes"]
    plan["plan_token"] = _maintenance_plan_token(plan)
    monkeypatch.setattr(resource, "_orphan_retention_metadata", lambda **_: (plan, object()))

    result = resource.cleanup_orphan_files(table_name="raw.events", catalog="iceberg", dry_run=True)

    assert result["planned"]["unavailable_fields"] == ["candidate_age", "affected_bytes"]
    assert result["planned"]["candidate_files"][0]["path"].endswith("orphan.parquet")


def test_orphan_execute_is_blocked_and_non_retryable(monkeypatch) -> None:
    resource = IcebergResource(ref="main")
    plan = _plan("cleanup_orphan_files")
    plan["candidate_files"] = [{"path": "orphan.parquet"}]
    plan["affected_objects"] = 1
    plan["affected_bytes"] = 100
    plan["plan_token"] = _maintenance_plan_token(plan)
    monkeypatch.setattr(resource, "_orphan_retention_metadata", lambda **_: (plan, object()))

    result = resource.cleanup_orphan_files(
        table_name="raw.events",
        catalog="iceberg",
        dry_run=False,
        expected_snapshot_id=41,
        confirmation_token=plan["plan_token"],
        max_affected_objects=10,
        max_affected_bytes=1000,
    )

    assert result["status"] == "blocked"
    assert result["failure"]["code"] == "bounded_execution_unsupported"
    assert result["failure"]["retryable"] is False
    assert result["retry_safe"] is False
    assert result["planned"]["trino_boundary"] == "not_invoked"


def test_orphan_race_discovers_extra_candidate_and_submits_nothing(monkeypatch) -> None:
    resource = IcebergResource(ref="main")
    plan = _plan("cleanup_orphan_files")
    plan["candidate_files"] = [{"path": "orphan.parquet"}]
    plan["affected_objects"] = 1
    plan["affected_bytes"] = 100
    plan["plan_token"] = _maintenance_plan_token(plan)
    monkeypatch.setattr(resource, "_orphan_retention_metadata", lambda **_: (plan, object()))
    planned = resource.cleanup_orphan_files(
        table_name="raw.events", catalog="iceberg", dry_run=True
    )

    extra = dict(plan)
    extra["candidate_files"] = [*plan["candidate_files"], {"path": "extra.parquet"}]
    extra["affected_objects"] = 2
    extra["plan_token"] = _maintenance_plan_token(extra)
    monkeypatch.setattr(resource, "_orphan_retention_metadata", lambda **_: (extra, object()))
    result = resource.cleanup_orphan_files(
        table_name="raw.events",
        catalog="iceberg",
        dry_run=False,
        expected_snapshot_id=41,
        confirmation_token=planned["plan_token"],
        max_affected_objects=10,
        max_affected_bytes=1000,
    )

    assert result["status"] == "blocked"
    assert result["failure"]["code"] == "plan_token_invalid"
    assert result["planned"]["trino_boundary"] == "not_invoked"


def test_legacy_snapshot_helper_cannot_bypass_plan_first() -> None:
    from phlo_iceberg.tables import expire_snapshots

    with pytest.raises(ValueError, match="plan-first"):
        expire_snapshots("raw.events")
