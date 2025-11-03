# jobs.py - Dagster job definitions for orchestrating the Nightscout data pipeline
# Defines asset jobs that group and schedule related data transformation tasks
# for the end-to-end glucose data processing workflow

from __future__ import annotations

import dagster as dg

from cascade.defs.partitions import daily_partition
from cascade.defs.jobs import JOBS, nightscout_job, github_job, publish_job, dev_pipeline_job, prod_promotion_job


# --- Helper Functions ---
# Functions for building Dagster definitions
def build_defs() -> dg.Definitions:
    return dg.Definitions(jobs=[nightscout_job, github_job, publish_job, dev_pipeline_job, prod_promotion_job])
