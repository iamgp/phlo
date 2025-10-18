"""
Branch-aware workflow orchestration for dev/prod isolation.

This module defines jobs and schedules that integrate Nessie branching
into the data pipeline, enabling development/production workflows.
"""

from __future__ import annotations

import dagster as dg

from cascade.defs.partitions import daily_partition


DEV_PIPELINE_JOB = dg.define_asset_job(
    name="dev_pipeline",
    description="Development pipeline: runs on dev branch with branch isolation",
    selection=(
        dg.AssetSelection.keys("nessie_dev_branch")
        | dg.AssetSelection.groups("ingestion", "bronze", "silver", "gold")
    ),
    partitions_def=daily_partition,
    config={
        "resources": {
            "iceberg": {"config": {"ref": "dev"}},
            "trino": {"config": {"nessie_ref": "dev"}},
        },
        "ops": {
            "all_dbt_assets": {
                "config": {
                    "target": "dev",
                }
            }
        }
    },
)

PROD_PROMOTION_JOB = dg.define_asset_job(
    name="prod_promotion",
    description="Production promotion: merge dev to main and publish marts to postgres",
    selection=(
        dg.AssetSelection.keys("promote_dev_to_main") | dg.AssetSelection.groups("publish")
    ),
    config={
        "resources": {
            "iceberg": {"config": {"ref": "main"}},
            "trino": {"config": {"nessie_ref": "main"}},
        },
    },
)


def build_schedules() -> list[dg.ScheduleDefinition]:
    """
    Build schedules for automated dev pipeline execution.

    Development pipeline runs daily at 02:00 Europe/London time.
    Production promotion is manual (no schedule).
    """

    def _dev_pipeline_run_requests(
        context: dg.ScheduleEvaluationContext,
    ):
        scheduled = context.scheduled_execution_time
        if scheduled is None:
            raise RuntimeError(
                "dev_pipeline_schedule triggered without a scheduled execution time."
            )

        partition_key = daily_partition.get_partition_key_for_timestamp(scheduled)
        yield dg.RunRequest(partition_key=partition_key)

    dev_pipeline_schedule = dg.ScheduleDefinition(
        name="dev_pipeline_schedule",
        job=DEV_PIPELINE_JOB,
        cron_schedule="0 2 * * *",
        execution_timezone="Europe/London",
        default_status=dg.DefaultScheduleStatus.STOPPED,
        execution_fn=_dev_pipeline_run_requests,
    )

    return [dev_pipeline_schedule]


def build_sensors() -> list[dg.SensorDefinition]:
    """
    Build sensors for automated promotion based on quality checks.

    Currently returns empty list - promotion is manual.
    Future enhancement: auto-promote when quality checks pass.
    """
    return []


def build_defs() -> dg.Definitions:
    """Build workflow definitions for branch-aware pipelines."""
    return dg.Definitions(
        jobs=[DEV_PIPELINE_JOB, PROD_PROMOTION_JOB],
        schedules=build_schedules(),
        sensors=build_sensors(),
    )
