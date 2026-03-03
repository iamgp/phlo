"""
Write-Audit-Publish (WAP) lifecycle sensors for Dagster.

Automates the Nessie-backed WAP pattern:
1. Branch creation sensor — creates pipeline/run-{run_id} on job start.
2. Auto-promotion sensor — merges to main when all asset checks pass.
3. Branch cleanup sensor — deletes stale pipeline branches after retention.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import dagster as dg

from phlo.logging import get_logger

logger = get_logger(__name__)

WAP_BRANCH_PREFIX = "pipeline/"
WAP_TAG_KEY = "phlo/wap_branch"
DEFAULT_RETENTION_HOURS = 24
DEFAULT_CLEANUP_INTERVAL_SECONDS = 3600
DEFAULT_PROMOTION_INTERVAL_SECONDS = 60


def _load_nessie() -> Any:
    """Load NessieResource lazily so the base package works without phlo-nessie."""
    try:
        from phlo_nessie.resource import NessieResource
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "WAP sensors require phlo-nessie. Install phlo-dagster[nessie] or phlo-nessie."
        ) from exc
    return NessieResource


def _wap_branch_name(run_id: str) -> str:
    """Derive the WAP branch name for a run."""
    return f"{WAP_BRANCH_PREFIX}run-{run_id}"


# ---------------------------------------------------------------------------
# Sensor 1: Branch creation
# ---------------------------------------------------------------------------


@dg.sensor(
    name="wap_branch_creation_sensor",
    description="Creates an isolated Nessie branch for each new pipeline run (WAP write phase)",
    minimum_interval_seconds=30,
)
def wap_branch_creation_sensor(context: dg.SensorEvaluationContext):
    """Create a pipeline/run-{run_id} branch when a new run starts.

    Scans for STARTED runs that don't yet have a WAP branch tag, creates the
    branch in Nessie, and tags the run so downstream sensors can track it.
    """
    instance = context.instance
    NessieResource = _load_nessie()
    nessie = NessieResource()

    evaluation_time = datetime.now(timezone.utc)
    cursor_ts = None
    if context.cursor:
        try:
            cursor_ts = datetime.fromisoformat(context.cursor)
        except ValueError:
            cursor_ts = None

    cutoff = (
        (cursor_ts - timedelta(minutes=5))
        if cursor_ts
        else (evaluation_time - timedelta(minutes=5))
    )

    started_runs = list(
        instance.get_runs(
            filters=dg.RunsFilter(
                statuses=[dg.DagsterRunStatus.STARTED],
                updated_after=cutoff,
            )
        )
    )

    branches_created = 0

    for run in started_runs:
        run_tags = run.tags or {}
        if WAP_TAG_KEY in run_tags:
            continue

        branch_name = _wap_branch_name(run.run_id)

        branch_hash = nessie.create_branch(branch_name, from_ref="main")
        if branch_hash is None:
            logger.warning(
                "wap_branch_creation_skipped",
                run_id=run.run_id,
                branch_name=branch_name,
            )
            continue

        instance.add_run_tags(run.run_id, {WAP_TAG_KEY: branch_name})
        branches_created += 1
        logger.info(
            "wap_branch_created",
            run_id=run.run_id,
            branch_name=branch_name,
            branch_hash=branch_hash,
        )

    if branches_created:
        logger.info(
            "wap_branch_creation_sensor_completed",
            branches_created=branches_created,
            scanned_runs=len(started_runs),
        )

    context.update_cursor(evaluation_time.isoformat())


# ---------------------------------------------------------------------------
# Sensor 2: Auto-promotion (audit → publish)
# ---------------------------------------------------------------------------


@dg.sensor(
    name="wap_auto_promotion_sensor",
    description="Merges WAP branches to main when all asset checks pass (WAP publish phase)",
    minimum_interval_seconds=DEFAULT_PROMOTION_INTERVAL_SECONDS,
)
def wap_auto_promotion_sensor(context: dg.SensorEvaluationContext):
    """Merge pipeline branches whose runs succeeded with all checks passing.

    Scans for SUCCESS runs tagged with a WAP branch. For each, verifies that
    no asset checks failed, then merges the branch to main and cleans up.
    """
    instance = context.instance
    NessieResource = _load_nessie()
    nessie = NessieResource()

    evaluation_time = datetime.now(timezone.utc)
    cursor_ts = None
    if context.cursor:
        try:
            cursor_ts = datetime.fromisoformat(context.cursor)
        except ValueError:
            cursor_ts = None

    cutoff = (
        (cursor_ts - timedelta(minutes=5)) if cursor_ts else (evaluation_time - timedelta(hours=1))
    )

    success_runs = list(
        instance.get_runs(
            filters=dg.RunsFilter(
                statuses=[dg.DagsterRunStatus.SUCCESS],
                updated_after=cutoff,
            )
        )
    )

    promoted = 0
    blocked = 0

    for run in success_runs:
        run_tags = run.tags or {}
        branch_name = run_tags.get(WAP_TAG_KEY)
        if not branch_name:
            continue

        if run_tags.get("phlo/wap_promoted"):
            continue

        if not _all_checks_passed(instance, run.run_id):
            blocked += 1
            logger.info(
                "wap_promotion_blocked_quality",
                run_id=run.run_id,
                branch_name=branch_name,
            )
            continue

        merged = nessie.merge_branch(source=branch_name, target="main")
        if not merged:
            logger.error(
                "wap_promotion_merge_failed",
                run_id=run.run_id,
                branch_name=branch_name,
            )
            continue

        nessie.delete_branch(branch_name)
        instance.add_run_tags(run.run_id, {"phlo/wap_promoted": "true"})
        promoted += 1
        logger.info(
            "wap_branch_promoted",
            run_id=run.run_id,
            branch_name=branch_name,
        )

    if promoted or blocked:
        logger.info(
            "wap_auto_promotion_sensor_completed",
            promoted=promoted,
            blocked=blocked,
            scanned_runs=len(success_runs),
        )

    context.update_cursor(evaluation_time.isoformat())


def _all_checks_passed(instance: Any, run_id: str) -> bool:
    """Return True if every asset check in the run passed (or none were executed)."""
    check_events = list(
        instance.get_event_log_entries(
            run_id=run_id,
            event_filter_fn=lambda event: (
                event.event_type == dg.DagsterEventType.ASSET_CHECK_EVALUATION
            ),
        )
    )
    for event in check_events:
        check_eval = event.asset_check_evaluation
        if check_eval is not None and not check_eval.passed:
            return False
    return True


# ---------------------------------------------------------------------------
# Sensor 3: Branch cleanup
# ---------------------------------------------------------------------------


@dg.sensor(
    name="wap_branch_cleanup_sensor",
    description="Deletes stale WAP pipeline branches past retention period",
    minimum_interval_seconds=DEFAULT_CLEANUP_INTERVAL_SECONDS,
)
def wap_branch_cleanup_sensor(context: dg.SensorEvaluationContext):
    """Clean up pipeline branches older than the retention period.

    Scans Nessie for branches matching the pipeline/ prefix and deletes those
    whose associated runs have terminated (SUCCESS or FAILURE) and whose
    creation time exceeds the retention window.
    """
    NessieResource = _load_nessie()
    nessie = NessieResource()

    retention_cutoff = datetime.now(timezone.utc) - timedelta(hours=DEFAULT_RETENTION_HOURS)

    branches = nessie.list_branches()
    pipeline_branches = [b for b in branches if b.name.startswith(WAP_BRANCH_PREFIX)]

    deleted = 0
    skipped = 0

    for branch in pipeline_branches:
        if not branch.created_at or branch.created_at > retention_cutoff:
            skipped += 1
            continue

        if nessie.delete_branch(branch.name):
            deleted += 1
            logger.info(
                "wap_branch_cleaned_up",
                branch_name=branch.name,
                created_at=branch.created_at.isoformat() if branch.created_at else None,
            )
        else:
            logger.warning(
                "wap_branch_cleanup_failed",
                branch_name=branch.name,
            )

    if deleted or skipped:
        logger.info(
            "wap_branch_cleanup_sensor_completed",
            deleted=deleted,
            skipped=skipped,
            total_pipeline_branches=len(pipeline_branches),
        )


# ---------------------------------------------------------------------------
# Definitions helper
# ---------------------------------------------------------------------------


def get_wap_definitions() -> dg.Definitions:
    """Return Dagster definitions for the WAP lifecycle sensors.

    Merge into your project definitions to enable automated
    Write-Audit-Publish:

        ```python
        from phlo_dagster.wap_sensors import get_wap_definitions

        defs = dg.Definitions.merge(your_defs, get_wap_definitions())
        ```
    """
    logger.info(
        "dagster_wap_definitions_built",
        sensor_count=3,
    )
    return dg.Definitions(
        sensors=[
            wap_branch_creation_sensor,
            wap_auto_promotion_sensor,
            wap_branch_cleanup_sensor,
        ],
    )
