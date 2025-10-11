from __future__ import annotations

import dagster as dg


def build_asset_jobs() -> list[dg.UnresolvedAssetJobDefinition]:
    ingest_job = dg.define_asset_job(
        name="ingest_raw_data",
        selection=dg.AssetSelection.groups("raw_ingestion"),
        description="Sync data from sources via Airbyte",
    )

    transform_job = dg.define_asset_job(
        name="transform_dbt_models",
        selection=dg.AssetSelection.all(),
        description="Run all dbt models: staging → intermediate → curated → marts",
    )

    return [ingest_job, transform_job]


def build_schedules(transform_job: dg.UnresolvedAssetJobDefinition) -> list[dg.ScheduleDefinition]:
    nightly_pipeline_schedule = dg.ScheduleDefinition(
        name="nightly_pipeline",
        job=transform_job,
        cron_schedule="0 2 * * *",
        execution_timezone="Europe/London",
    )

    return [nightly_pipeline_schedule]
