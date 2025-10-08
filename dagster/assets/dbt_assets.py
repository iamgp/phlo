import os
from pathlib import Path
from dagster import AssetExecutionContext, asset, Output
from dagster_dbt import DbtCliResource

DBT_PROJECT_DIR = Path("/dbt")
DBT_PROFILES_DIR = Path("/dbt/profiles")

# Asset-based dbt models using op-based approach
# This allows us to dynamically load dbt without requiring manifest.json at definition time

@asset(
    group_name="dbt_staging",
    description="Staging layer - reads raw parquet files",
)
def dbt_staging_models(context: AssetExecutionContext, dbt: DbtCliResource):
    """Run dbt staging models (stg_*)"""
    openlineage_env = {
        "OPENLINEAGE_URL": os.getenv("OPENLINEAGE_URL", "http://marquez:5000"),
        "OPENLINEAGE_NAMESPACE": os.getenv("OPENLINEAGE_NAMESPACE", "lakehouse"),
        "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
    }

    result = dbt.cli(["run", "--select", "tag:stg"], context=context, env=openlineage_env).wait()
    context.log.info(f"dbt staging models completed: {result.success}")
    return Output({"success": result.success})


@asset(
    group_name="dbt_curated",
    description="Curated layer - cleaned and enriched data",
    deps=[dbt_staging_models],
)
def dbt_curated_models(context: AssetExecutionContext, dbt: DbtCliResource):
    """Run dbt curated models (intermediate + curated)"""
    openlineage_env = {
        "OPENLINEAGE_URL": os.getenv("OPENLINEAGE_URL", "http://marquez:5000"),
        "OPENLINEAGE_NAMESPACE": os.getenv("OPENLINEAGE_NAMESPACE", "lakehouse"),
        "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
    }

    result = dbt.cli(
        ["run", "--select", "tag:int tag:curated"],
        context=context,
        env=openlineage_env
    ).wait()
    context.log.info(f"dbt curated models completed: {result.success}")
    return Output({"success": result.success})


@asset(
    group_name="dbt_marts",
    description="Data marts in Postgres for analytics and BI",
    deps=[dbt_curated_models],
)
def dbt_postgres_marts(context: AssetExecutionContext, dbt: DbtCliResource):
    """Run dbt mart models targeting Postgres"""
    openlineage_env = {
        "OPENLINEAGE_URL": os.getenv("OPENLINEAGE_URL", "http://marquez:5000"),
        "OPENLINEAGE_NAMESPACE": os.getenv("OPENLINEAGE_NAMESPACE", "lakehouse"),
        "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
    }

    result = dbt.cli(
        ["run", "--select", "tag:mart", "--target", "postgres"],
        context=context,
        env=openlineage_env
    ).wait()
    context.log.info(f"dbt postgres marts completed: {result.success}")
    return Output({"success": result.success})
