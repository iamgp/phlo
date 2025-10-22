# jobs.py - Dagster job definitions for orchestrating the Nightscout data pipeline
# Defines asset jobs that group and schedule related data transformation tasks
# for the end-to-end glucose data processing workflow

from __future__ import annotations

import dagster as dg

from cascade.defs.partitions import daily_partition


# --- Job Definitions ---
# Asset jobs that orchestrate the complete data pipeline
nightscout_job = dg.define_asset_job(
    name="nightscout_pipeline",
    selection=["group:nightscout"],
    partitions_def=daily_partition,
)

github_job = dg.define_asset_job(
name="github_pipeline",
selection=["group:github"],
partitions_def=daily_partition,
)

# Publishing job for all marts
publish_job = dg.define_asset_job(
    name="publish_pipeline",
    selection=["publish_glucose_marts_to_postgres"],
)


# --- Helper Functions ---
# Functions for building Dagster definitions
def build_defs() -> dg.Definitions:
    return dg.Definitions(jobs=[nightscout_job, github_job])
