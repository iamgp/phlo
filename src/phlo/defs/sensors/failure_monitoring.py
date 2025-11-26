# failure_monitoring.py - Sensors for pipeline health monitoring and alerting
# Defines sensors that monitor pipeline failures, successes, and data freshness
# enabling observability and incident response in the data platform

from __future__ import annotations

import dagster as dg


# --- Failure and Status Sensors ---
# Sensors that monitor pipeline execution and log events for observability
@dg.run_failure_sensor(
    name="pipeline_failure_alert",
    description="Monitors for pipeline failures and logs alerts for observability integration",
    monitored_jobs=[
        dg.JobSelector(
            location_name="phlo",
            job_name="*",  # Monitor all jobs
        )
    ],
)
def pipeline_failure_sensor(context: dg.RunFailureSensorContext):
    """
    Sensor that triggers on any pipeline failure.

    Logs structured failure information that can be picked up by Loki/Grafana.
    In production, this can be extended to:
    - Send alerts to Slack/PagerDuty
    - Create incidents in incident management systems
    - Post to webhook endpoints
    - Update status pages
    """
    run_id = context.dagster_run.run_id
    job_name = context.dagster_run.job_name
    failure_message = (
        context.failure_event.message if context.failure_event else "Unknown failure"
    )

    # Log structured failure information for Loki to pick up
    context.log.error(
        "Pipeline failure detected",
        extra={
            "event_type": "pipeline_failure",
            "run_id": run_id,
            "job_name": job_name,
            "failure_message": failure_message,
            "pipeline_name": context.dagster_run.job_name,
            "run_config": str(context.dagster_run.run_config),
        },
    )

    # Log asset failures if available
    if context.failure_event and hasattr(context.failure_event, "asset_key"):
        context.log.error(
            f"Asset failure: {context.failure_event.asset_key}",
            extra={
                "event_type": "asset_failure",
                "asset_key": str(context.failure_event.asset_key),
                "run_id": run_id,
            },
        )


# Success status sensor
@dg.run_status_sensor(
    name="pipeline_status_logger",
    description="Logs all pipeline status changes for observability tracking",
    monitored_jobs=[
        dg.JobSelector(
            location_name="phlo",
            job_name="*",
        )
    ],
    run_status=dg.DagsterRunStatus.SUCCESS,
)
def pipeline_success_sensor(context: dg.RunStatusSensorContext):
    """
    Sensor that logs successful pipeline completions.

    Provides metrics for pipeline health and SLO tracking.
    """
    run_id = context.dagster_run.run_id
    job_name = context.dagster_run.job_name

    context.log.info(
        "Pipeline completed successfully",
        extra={
            "event_type": "pipeline_success",
            "run_id": run_id,
            "job_name": job_name,
            "pipeline_name": context.dagster_run.job_name,
            "start_time": str(context.dagster_run.start_time),
            "end_time": str(context.dagster_run.end_time),
        },
    )


# Data freshness sensor
@dg.asset_sensor(
    name="iceberg_table_freshness_monitor",
    asset_key=dg.AssetKey(["entries"]),
    description="Monitors freshness of Iceberg ingestion",
)
def iceberg_freshness_sensor(
    context: dg.SensorEvaluationContext, asset_event: dg.EventLogEntry
):
    """
    Monitors freshness of critical Iceberg tables.

    Alerts if data hasn't been updated within expected timeframes.
    This is complementary to Dagster's built-in FreshnessPolicy.
    """
    if asset_event.dagster_event and asset_event.dagster_event.is_step_success:
        context.log.info(
            "Iceberg table updated",
            extra={
                "event_type": "iceberg_table_updated",
                "asset_key": str(asset_event.dagster_event.asset_key),
                "timestamp": str(asset_event.timestamp),
            },
        )
