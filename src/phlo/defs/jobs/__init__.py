# __init__.py - Jobs module initialization
# Provides job factory utilities for creating jobs from config

from __future__ import annotations

from typing import Any

import dagster as dg

from .factory import create_jobs_from_config

# Jobs are user-defined - framework returns empty list by default
JOBS: list[Any] = []

# Create a lookup dictionary for jobs by name
JOB_LOOKUP = {job.name: job for job in JOBS}


def get_job(name: str) -> dg.JobDefinition | None:
    """Get a job by name."""
    return JOB_LOOKUP.get(name)


__all__ = ["JOBS", "JOB_LOOKUP", "get_job", "create_jobs_from_config"]
