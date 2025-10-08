import os
from dagster import op, job
from dagster_dbt import DbtCliResource

@op
def dbt_run_all(context, dbt: DbtCliResource):
    # Set OpenLineage environment variables for dbt
    openlineage_env = {
        "OPENLINEAGE_URL": os.getenv("OPENLINEAGE_URL", "http://marquez:5000"),
        "OPENLINEAGE_NAMESPACE": os.getenv("OPENLINEAGE_NAMESPACE", "lakehouse"),
        "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
    }

    dbt_cli_invocation = dbt.cli(
        ["run"],
        context=context,
        env=openlineage_env
    )
    return dbt_cli_invocation.wait()

@op
def dbt_test_all(context, dbt: DbtCliResource):
    openlineage_env = {
        "OPENLINEAGE_URL": os.getenv("OPENLINEAGE_URL", "http://marquez:5000"),
        "OPENLINEAGE_NAMESPACE": os.getenv("OPENLINEAGE_NAMESPACE", "lakehouse"),
        "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
    }

    dbt_cli_invocation = dbt.cli(
        ["test"],
        context=context,
        env=openlineage_env
    )
    return dbt_cli_invocation.wait()

@job(
    resource_defs={
        "dbt": DbtCliResource(
            project_dir="/dbt",
            profiles_dir="/dbt/profiles",
        )
    }
)
def dbt_build_duckdb_then_marts():
    # In dbt, use selectors to: 1) build duckdb targets, 2) build postgres marts
    dbt_run_all()
    dbt_test_all()
