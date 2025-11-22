# jobs.py - Dagster job definitions for orchestrating the Cascade data pipeline
# Defines asset jobs that group and schedule related data transformation tasks
# Provides a build_defs function for integration into the main definitions

from __future__ import annotations

import dagster as dg

from phlo.defs.jobs import (
    nightscout_job,
    github_job,
    publish_job,
    full_pipeline_job,
)


# --- Helper Functions ---
# Functions for building Dagster definitions
def build_defs() -> dg.Definitions:
    """Build job definitions for the Cascade pipeline."""
    return dg.Definitions(
        jobs=[
            nightscout_job,
            github_job,
            publish_job,
            full_pipeline_job,
        ]
    )
