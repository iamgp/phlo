from __future__ import annotations

import dagster as dg

from lakehousekit.defs.partitions import daily_partition


def build_asset_jobs() -> list[dg.UnresolvedAssetJobDefinition]:
    """
    Build Dagster job definitions for the lakehouse pipeline.

    Returns:
        List of job definitions:
        - ingest_raw_data: Syncs data from external sources via Airbyte
        - transform_dbt_models: Runs complete dbt transformation pipeline
    """
    ingest_job = dg.define_asset_job(
        name="ingest_raw_data",
        selection=dg.AssetSelection.groups("raw_ingestion"),
        description="Sync data from sources via Airbyte",
    )

    transform_job = dg.define_asset_job(
        name="transform_dbt_models",
        selection=dg.AssetSelection.all(),
        description="Run all dbt models: staging → intermediate → curated → marts",
        partitions_def=daily_partition,
    )

    return [ingest_job, transform_job]


def build_schedules(
    transform_job: dg.UnresolvedAssetJobDefinition,
) -> list[dg.ScheduleDefinition]:
    """
    Build schedule definitions for automated pipeline execution.

    Args:
        transform_job: The dbt transformation job to schedule

    Returns:
        List of schedule definitions:
        - nightly_pipeline: Runs dbt transformations daily at 2am Europe/London
    """
    nightly_pipeline_schedule = dg.ScheduleDefinition(
        name="nightly_pipeline",
        job=transform_job,
        cron_schedule="0 2 * * *",
        execution_timezone="Europe/London",
    )

    return [nightly_pipeline_schedule]
