"""Tests for automated table maintenance policies."""

from __future__ import annotations

from phlo_dagster.maintenance_policy import (
    ExpireSnapshotsPolicy,
    NamespacePolicy,
    OptimizePolicy,
    evaluate_table,
    load_policies,
)


def test_evaluate_table_triggers_expire() -> None:
    """Expire is triggered when snapshot_count exceeds the threshold."""
    policy = NamespacePolicy(
        namespace="raw",
        expire=ExpireSnapshotsPolicy(snapshot_count_gt=10),
    )
    stats = {"snapshot_count": 15, "total_size_mb": 100.0, "file_count": 5}

    action = evaluate_table("raw.my_table", stats, policy)

    assert action.expire_snapshots is True
    assert action.table_name == "raw.my_table"


def test_evaluate_table_no_expire() -> None:
    """Expire is not triggered when snapshot_count is at or below the threshold."""
    policy = NamespacePolicy(
        namespace="raw",
        expire=ExpireSnapshotsPolicy(snapshot_count_gt=20),
    )
    stats = {"snapshot_count": 20, "total_size_mb": 100.0, "file_count": 5}

    action = evaluate_table("raw.my_table", stats, policy)

    assert action.expire_snapshots is False


def test_evaluate_table_triggers_optimize() -> None:
    """Optimize is triggered when average file size is below the threshold."""
    policy = NamespacePolicy(
        namespace="raw",
        optimize=OptimizePolicy(avg_file_size_mb_lt=64.0),
    )
    # avg = 100 / 10 = 10 MB, below 64
    stats = {"snapshot_count": 5, "total_size_mb": 100.0, "file_count": 10}

    action = evaluate_table("raw.my_table", stats, policy)

    assert action.optimize is True


def test_evaluate_table_no_optimize() -> None:
    """Optimize is not triggered when average file size meets the threshold."""
    policy = NamespacePolicy(
        namespace="raw",
        optimize=OptimizePolicy(avg_file_size_mb_lt=64.0),
    )
    # avg = 640 / 10 = 64 MB, not below 64
    stats = {"snapshot_count": 5, "total_size_mb": 640.0, "file_count": 10}

    action = evaluate_table("raw.my_table", stats, policy)

    assert action.optimize is False


def test_evaluate_table_missing_stats_skips_optimize() -> None:
    """Optimize is skipped when file_count is 0 (avoids division by zero)."""
    policy = NamespacePolicy(
        namespace="raw",
        optimize=OptimizePolicy(avg_file_size_mb_lt=64.0),
    )
    stats = {"snapshot_count": 5, "total_size_mb": 0.0, "file_count": 0}

    action = evaluate_table("raw.my_table", stats, policy)

    assert action.optimize is False


def test_load_policies_yaml(tmp_path) -> None:
    """Policies are correctly parsed from a YAML file."""
    policy_file = tmp_path / "policies.yaml"
    policy_file.write_text(
        """\
policies:
  - namespace: raw
    expire:
      snapshot_count_gt: 25
      older_than_days: 14
      retain_last: 3
    optimize:
      avg_file_size_mb_lt: 32.0
  - namespace: curated
    ref: dev
    expire:
      snapshot_count_gt: 10
"""
    )

    policies = load_policies(policy_file)

    assert len(policies) == 2

    raw = policies[0]
    assert raw.namespace == "raw"
    assert raw.ref == "main"
    assert raw.expire is not None
    assert raw.expire.snapshot_count_gt == 25
    assert raw.expire.older_than_days == 14
    assert raw.expire.retain_last == 3
    assert raw.optimize is not None
    assert raw.optimize.avg_file_size_mb_lt == 32.0

    curated = policies[1]
    assert curated.namespace == "curated"
    assert curated.ref == "dev"
    assert curated.expire is not None
    assert curated.expire.snapshot_count_gt == 10
    assert curated.optimize is None


def test_get_policy_maintenance_definitions_returns_sensor() -> None:
    """get_policy_maintenance_definitions includes the sensor and optimize job."""
    from phlo_dagster.maintenance_sensor import get_policy_maintenance_definitions

    defs = get_policy_maintenance_definitions()

    sensor_names = [s.name for s in defs.sensors]
    job_names = [j.name for j in defs.jobs]

    assert "maintenance_policy_sensor" in sensor_names
    assert "optimize_tables_job" in job_names
