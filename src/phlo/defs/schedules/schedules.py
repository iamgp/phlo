# schedules.py - Factory for schedules defined in code
# Schedules are complex and workflow-specific, so they stay in code

from __future__ import annotations

from typing import List
from phlo.defs.jobs import full_pipeline_job

import dagster as dg


def create_schedules(jobs: List[dg.UnresolvedAssetJobDefinition]) -> List[dg.ScheduleDefinition]:
    """
    Create schedule definitions in code.
    Schedules are complex and workflow-specific, so they remain in code rather than YAML.
    """

    def _full_pipeline_run_requests(context: dg.ScheduleEvaluationContext):
        """Execution function for full pipeline schedule."""
        scheduled = context.scheduled_execution_time
        if scheduled is None:
            raise RuntimeError("full_pipeline_schedule triggered without scheduled execution time")

        # Use the job's partitions if it has them
        if hasattr(full_pipeline_job, 'partitions_def') and full_pipeline_job.partitions_def:
            partition_key = full_pipeline_job.partitions_def.get_partition_key_for_timestamp(scheduled)
            yield dg.RunRequest(partition_key=partition_key)
        else:
            yield dg.RunRequest()

    # Full pipeline schedule (ingestion -> transform -> validation -> auto-promote)
    full_pipeline_schedule = dg.ScheduleDefinition(
        name="full_pipeline_schedule",
        job=full_pipeline_job,
        cron_schedule="0 2 * * *",  # Daily at 2:00 AM
        execution_timezone="Europe/London",
        default_status=dg.DefaultScheduleStatus.STOPPED,  # Start stopped for safety
        execution_fn=_full_pipeline_run_requests,
    )

    return [full_pipeline_schedule]
