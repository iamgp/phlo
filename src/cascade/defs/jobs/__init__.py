# __init__.py - Jobs module initialization
# Provides job definitions for the data pipeline

import dagster as dg
from cascade.defs.partitions import daily_partition
from .factory import create_jobs_from_config

# Load all jobs
JOBS = create_jobs_from_config() + [
    # Transform job (complex asset selection, so defined here)
    dg.define_asset_job(
        name="transform_dbt_models",
        selection=dg.AssetSelection.groups(
            "github",
            "nightscout",
            "transform",
        ),
        partitions_def=daily_partition,
    )
]

# Create a lookup dictionary for jobs by name
JOB_LOOKUP = {job.name: job for job in JOBS}

# Helper function to get job by name
def get_job(name: str):
    """Get a job by name."""
    return JOB_LOOKUP.get(name)

# Expose individual jobs for easy access
transform_job = get_job("transform_dbt_models")
nightscout_job = get_job("nightscout_pipeline")
github_job = get_job("github_pipeline")
publish_job = get_job("publish_pipeline")
dev_pipeline_job = get_job("dev_pipeline")
prod_promotion_job = get_job("prod_promotion")
