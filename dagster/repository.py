from dagster import Definitions
from jobs.ingest_airbyte import airbyte_ingest_job
from jobs.transform_dbt import dbt_build_duckdb_then_marts
from jobs.validate_ge import ge_prepost_validation_job
from schedules.nightly import nightly_all

defs = Definitions(
    jobs=[
        ge_prepost_validation_job,
        dbt_build_duckdb_then_marts,
        airbyte_ingest_job,            # no-op unless Airbyte profile is up
    ],
    schedules=[nightly_all],
)
