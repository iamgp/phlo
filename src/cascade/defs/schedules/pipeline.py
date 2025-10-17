from __future__ import annotations

import dagster as dg
from dagster import AssetKey, RunRequest, SensorEvaluationContext, asset_sensor

from cascade.defs.partitions import daily_partition

# Define jobs once so schedules and other consumers share the same definitions.
INGEST_JOB = dg.define_asset_job(
    name="ingest_raw_data",
    selection=dg.AssetSelection.groups("ingestion"),
    partitions_def=daily_partition,
)

TRANSFORM_JOB = dg.define_asset_job(
    name="transform_dbt_models",
    selection=dg.AssetSelection.groups(
        "bronze",
        "silver",
        "gold",
        "publish",
    ),
    partitions_def=daily_partition,
)


def build_asset_jobs() -> list[dg.UnresolvedAssetJobDefinition]:
    """Expose asset-driven jobs for manual and sensor-triggered execution."""
    return [INGEST_JOB, TRANSFORM_JOB]


def build_sensors() -> list[dg.SensorDefinition]:
    """
    Trigger downstream transformations whenever fresh Nightscout data lands in Iceberg raw layer.

    We monitor the partitioned entries asset and fan out matching partition keys to the dbt job
    so every ingestion run immediately promotes the corresponding day through the warehouse.
    """

    @asset_sensor(
        asset_key=AssetKey(["entries"]),
        job_name=TRANSFORM_JOB.name,
        minimum_interval_seconds=300,  # Debounce: at most once every 5 minutes
    )
    def transform_on_new_nightscout_data(
        context: SensorEvaluationContext,
        asset_event: dg.EventLogEntry,
    ):
        # Check if new data exists
        metadata = asset_event.dagster_event.event_specific_data.materialization.asset_materialization.metadata
        rows_loaded = metadata.get("rows_loaded")
        if rows_loaded is None or rows_loaded.value <= 0:
            return  # No new data, skip

        partition_key = asset_event.partition
        cursor = str(asset_event.storage_id)
        context.update_cursor(cursor)

        if partition_key:
            yield RunRequest(run_key=f"{cursor}:{partition_key}", partition_key=partition_key)
        else:
            yield RunRequest(run_key=cursor)

    return [transform_on_new_nightscout_data]


def build_schedules() -> list[dg.ScheduleDefinition]:
    """
    Provide a manual fallback schedule that backfills the daily ingestion partition at 02:00.
    """

    def _ingest_run_requests(
        context: dg.ScheduleEvaluationContext,
    ):
        scheduled = context.scheduled_execution_time
        if scheduled is None:
            raise RuntimeError(
                "daily_ingestion_fallback triggered without a scheduled execution time."
            )

        partition_key = daily_partition.get_partition_key_for_timestamp(scheduled)
        yield RunRequest(partition_key=partition_key)

    ingest_schedule = dg.ScheduleDefinition(
        name="daily_ingestion_fallback",
        job=INGEST_JOB,
        cron_schedule="0 2 * * *",
        execution_timezone="Europe/London",
        default_status=dg.DefaultScheduleStatus.STOPPED,
        execution_fn=_ingest_run_requests,
    )

    return [ingest_schedule]


def build_defs() -> dg.Definitions:
    """Aggregate the jobs, sensors, and schedules into Dagster definitions."""
    return dg.Definitions(
        jobs=build_asset_jobs(),
        sensors=build_sensors(),
        schedules=build_schedules(),
    )
