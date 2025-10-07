from dagster import job
from dagster_dbt import dbt_run_op, dbt_test_op

@job
def dbt_build_duckdb_then_marts():
    dbt_run = dbt_run_op()
    dbt_test = dbt_test_op()
    # In dbt, use selectors to: 1) build duckdb targets, 2) build postgres marts
    dbt_run.alias("run_all")()
    dbt_test.alias("test_all")()
