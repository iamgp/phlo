# factory.py - Factory for schedules defined in code
# Schedules are complex and workflow-specific, so they stay in code

from __future__ import annotations

from typing import List
from cascade.defs.partitions import daily_partition
from cascade.defs.jobs import dev_pipeline_job

import dagster as dg


def create_schedules(jobs: List[dg.UnresolvedAssetJobDefinition]) -> List[dg.ScheduleDefinition]:
    """
    Create schedule definitions in code.
    Schedules are complex and workflow-specific, so they remain in code rather than YAML.
    """

    def _dev_pipeline_run_requests(context: dg.ScheduleEvaluationContext):
        """Execution function for dev pipeline schedule."""
        scheduled = context.scheduled_execution_time
        if scheduled is None:
            raise RuntimeError("dev_pipeline_schedule triggered without scheduled execution time")

        # Use the job's partitions if it has them
        if hasattr(dev_pipeline_job, 'partitions_def') and dev_pipeline_job.partitions_def:
            partition_key = dev_pipeline_job.partitions_def.get_partition_key_for_timestamp(scheduled)
            yield dg.RunRequest(partition_key=partition_key)
        else:
            yield dg.RunRequest()

    # Development pipeline schedule
    dev_pipeline_schedule = dg.ScheduleDefinition(
        name="dev_pipeline_schedule",
        job=dev_pipeline_job,
        cron_schedule="0 2 * * *",  # Daily at 2:00 AM
        execution_timezone="Europe/London",
        default_status=dg.DefaultScheduleStatus.STOPPED,  # Start stopped for safety
        execution_fn=_dev_pipeline_run_requests,
    )

    # Add more schedules here as needed
    # For example:
    # prod_promotion_schedule = dg.ScheduleDefinition(
    #     name="prod_promotion_schedule",
    #     job=PROD_PROMOTION_JOB,
    #     cron_schedule="0 6 * * *",  # Daily at 6:00 AM
    #     execution_timezone="Europe/London",
    #     default_status=dg.DefaultScheduleStatus.RUNNING,
    #     execution_fn=_prod_promotion_run_requests,
    # )

    return [dev_pipeline_schedule]
