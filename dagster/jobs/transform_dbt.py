from dagster import job, op
from dagster_dbt import DbtCliResource


@op(required_resource_keys={"dbt"})
def dbt_run_all(context):
    context.resources.dbt.cli(["build"]).wait()


@op(required_resource_keys={"dbt"})
def dbt_test_all(context):
    context.resources.dbt.cli(["test"]).wait()


@job(
    resource_defs={
        "dbt": DbtCliResource(
            project_dir="/dbt",
            profiles_dir="/dbt/profiles",
        )
    }
)
def dbt_build_duckdb_then_marts():
    dbt_run_all()
    dbt_test_all()
