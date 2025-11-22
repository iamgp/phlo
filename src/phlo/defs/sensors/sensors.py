# pipeline.py - Pipeline orchestration definitions for the Nightscout data processing workflow
# Defines asset jobs, sensors, and schedules that coordinate the ingestion and transformation
# pipeline, enabling automated data flow from raw to processed analytics

from __future__ import annotations

import dagster as dg
from dagster import AssetKey, RunRequest, SensorEvaluationContext, asset_sensor

# Import the transform job for sensors
from phlo.defs.jobs import transform_job


def build_sensors() -> list[dg.SensorDefinition]:
    """
    Trigger downstream transformations whenever fresh data lands in Iceberg raw layer.

    We monitor the partitioned ingestion assets and fan out matching partition keys to the dbt job
    so every ingestion run immediately promotes the corresponding day through the warehouse.
    """

    @asset_sensor(
        asset_key=AssetKey(["dlt_glucose_entries"]),
        job=transform_job,
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

    @asset_sensor(
        asset_key=AssetKey(["dlt_github_user_events"]),
        job=transform_job,
        minimum_interval_seconds=300,  # Debounce: at most once every 5 minutes
    )
    def transform_on_new_github_user_events(
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

    @asset_sensor(
        asset_key=AssetKey(["dlt_github_repo_stats"]),
        job=transform_job,
        minimum_interval_seconds=300,  # Debounce: at most once every 5 minutes
    )
    def transform_on_new_github_repo_stats(
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

    return [transform_on_new_nightscout_data, transform_on_new_github_user_events, transform_on_new_github_repo_stats]





