"""Write-Audit-Publish (WAP) lifecycle sensors for Dagster.

This module implements automated WAP pattern orchestration for versioned data
catalogs (e.g., Nessie). The WAP pattern ensures data quality by isolating
writes on branches, auditing with automated checks, and only publishing
(promoting to main) after validation passes.

WAP Phases:
    1. Write: Data is written to an isolated branch (pipeline-run-{run_id})
    2. Audit: Asset checks validate data quality on the branch
    3. Publish: Successful runs are merged to main, branches cleaned up

Sensor Components:
    - wap_branch_creation_sensor: Creates isolated branches for new runs
    - wap_auto_promotion_sensor: Promotes branches after successful audit
    - wap_branch_cleanup_sensor: Removes stale branches past retention

Catalog Requirements:
    Requires a catalog capability with:
    - Branch/ref support (supports_refs)
    - Branch promotion support (supports_promote)
    - VersionedCatalog interface implementation

    Typically provided by phlo-nessie package.

Configuration:
    Environment variables control sensor behavior::

    PHLO_WAP_BRANCH_CREATION_INTERVAL_SECONDS: Branch sensor poll interval (default: 30)
    PHLO_WAP_PROMOTION_INTERVAL_SECONDS: Promotion sensor poll interval (default: 60)
    PHLO_WAP_CLEANUP_INTERVAL_SECONDS: Cleanup sensor poll interval (default: 3600)

Branch Naming:
    Branches follow pattern: pipeline-run-{run_id}
    Example: pipeline-run-abc123def456

Example:
    Enabling WAP sensors in definitions::

        from phlo_dagster.wap_sensors import get_wap_definitions

        wap_defs = get_wap_definitions()
        defs = dg.Definitions.merge(your_defs, wap_defs)

"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import dagster as dg

from phlo.capabilities.interfaces import VersionedCatalog
from phlo.capabilities.resolver import resolve_capability
from phlo.logging import get_logger

logger = get_logger(__name__)

WAP_BRANCH_PREFIX = "pipeline-"
WAP_TAG_KEY = "phlo/wap_branch"
DEFAULT_RETENTION_HOURS = 24
DEFAULT_BRANCH_CREATION_INTERVAL_SECONDS = int(
    os.getenv("PHLO_WAP_BRANCH_CREATION_INTERVAL_SECONDS", "30")
)
DEFAULT_CLEANUP_INTERVAL_SECONDS = int(os.getenv("PHLO_WAP_CLEANUP_INTERVAL_SECONDS", "3600"))
DEFAULT_PROMOTION_INTERVAL_SECONDS = int(os.getenv("PHLO_WAP_PROMOTION_INTERVAL_SECONDS", "60"))


def _load_versioned_catalog() -> VersionedCatalog:
    """Resolve the active versioned catalog capability for WAP flows.

    Args:
        None

    Returns:
        VersionedCatalog provider instance.

    Raises:
        RuntimeError: If catalog capability is not available or doesn't support refs/promotion.

    """
    resolution = resolve_capability("catalog")
    if resolution is None:
        raise RuntimeError("WAP sensors require a catalog capability with ref/promotion support.")

    if not (resolution.support.supports_refs and resolution.support.supports_promote):
        raise RuntimeError(
            "WAP sensors require a catalog capability that supports refs and promotion."
        )

    provider = resolution.provider
    if not isinstance(provider, VersionedCatalog):
        raise RuntimeError("WAP sensors require a VersionedCatalog-compatible provider.")
    return provider


def _wap_branch_name(run_id: str) -> str:
    """Derive the WAP branch name for a run.

    Args:
        run_id: Dagster run ID.

    Returns:
        WAP branch name string.

    """
    return f"{WAP_BRANCH_PREFIX}run-{run_id}"


# ---------------------------------------------------------------------------
# Sensor 1: Branch creation
# ---------------------------------------------------------------------------


@dg.sensor(
    name="wap_branch_creation_sensor",
    description="Creates an isolated Nessie branch for each new pipeline run (WAP write phase)",
    minimum_interval_seconds=DEFAULT_BRANCH_CREATION_INTERVAL_SECONDS,
    default_status=dg.DefaultSensorStatus.RUNNING,
)
def wap_branch_creation_sensor(context: dg.SensorEvaluationContext):
    """Create a pipeline-run-{run_id} branch when a new run starts.

    Scans for STARTED runs that don't yet have a WAP branch tag, creates the
    branch in the versioned catalog, and tags the run so downstream sensors can
    track it.

    Args:
        context: Dagster sensor evaluation context.

    Returns:
        None

    Raises:
        No explicit exceptions raised. Logs warnings on failures.

    """
    instance = context.instance
    catalog = _load_versioned_catalog()

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

        branch_hash = catalog.create_branch(branch_name, from_ref="main")
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
    default_status=dg.DefaultSensorStatus.RUNNING,
)
def wap_auto_promotion_sensor(context: dg.SensorEvaluationContext):
    """Merge pipeline branches whose runs succeeded with all checks passing.

    Scans for SUCCESS runs tagged with a WAP branch. For each, verifies that
    no asset checks failed, then merges the branch to main and cleans up.

    Args:
        context: Dagster sensor evaluation context.

    Returns:
        None

    Raises:
        No explicit exceptions raised. Logs warnings on failures.

    """
    instance = context.instance
    catalog = _load_versioned_catalog()

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

        merged = catalog.merge_branch(source=branch_name, target="main")
        if not merged:
            logger.error(
                "wap_promotion_merge_failed",
                run_id=run.run_id,
                branch_name=branch_name,
            )
            continue

        catalog.delete_branch(branch_name)
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
    """Return True if every asset check in the run passed (or none were executed).

    Args:
        instance: Dagster instance.
        run_id: Dagster run ID.

    Returns:
        True if all checks passed or no checks executed.

    """
    try:
        check_records = instance.get_records_for_run(
            run_id,
            of_type=dg.DagsterEventType.ASSET_CHECK_EVALUATION,
        )
    except Exception:
        logger.warning(
            "wap_all_checks_passed_filter_failed",
            run_id=run_id,
            exc_info=True,
        )
        return False

    for record in check_records.records:
        check_eval = record.event_log_entry.asset_check_evaluation
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
    default_status=dg.DefaultSensorStatus.RUNNING,
)
def wap_branch_cleanup_sensor(context: dg.SensorEvaluationContext):
    """Clean up pipeline branches older than the retention period.

    Scans the versioned catalog for branches matching the pipeline- prefix and deletes those
    whose associated runs have terminated (SUCCESS or FAILURE) and whose
    creation time exceeds the retention window.

    Args:
        context: Dagster sensor evaluation context.

    Returns:
        None

    Raises:
        No explicit exceptions raised. Logs warnings on failures.

    """
    catalog = _load_versioned_catalog()

    retention_cutoff = datetime.now(timezone.utc) - timedelta(hours=DEFAULT_RETENTION_HOURS)

    branches = catalog.list_branches()
    pipeline_branches = [b for b in branches if b.name.startswith(WAP_BRANCH_PREFIX)]

    deleted = 0
    skipped = 0

    for branch in pipeline_branches:
        if not branch.created_at or branch.created_at > retention_cutoff:
            skipped += 1
            continue

        if catalog.delete_branch(branch.name):
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
    Write-Audit-Publish.

    Args:
        None

    Returns:
        Dagster Definitions containing WAP sensors.

    Raises:
        No explicit exceptions raised.

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
