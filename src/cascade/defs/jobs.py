# jobs.py - Dagster job definitions for orchestrating the Nightscout data pipeline
# Defines asset jobs that group and schedule related data transformation tasks
# for the end-to-end glucose data processing workflow

from __future__ import annotations

import dagster as dg

from cascade.defs.partitions import daily_partition
from . import JOBS, nightscout_job, github_job, publish_job, DEV_PIPELINE_JOB, PROD_PROMOTION_JOB


# --- Helper Functions ---
# Functions for building Dagster definitions
def build_defs() -> dg.Definitions:
    return dg.Definitions(jobs=[nightscout_job, github_job, publish_job, DEV_PIPELINE_JOB, PROD_PROMOTION_JOB])
