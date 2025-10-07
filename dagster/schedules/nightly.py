from dagster import ScheduleDefinition
from ..repository import dbt_build_duckdb_then_marts

nightly_all = ScheduleDefinition(
    job=dbt_build_duckdb_then_marts,
    cron_schedule="0 2 * * *",  # 02:00 nightly
    execution_timezone="Europe/London",
)
