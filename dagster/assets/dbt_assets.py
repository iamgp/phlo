from pathlib import Path

from dagster import AssetExecutionContext, AssetKey
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets

DBT_PROJECT_DIR = Path("/dbt")
DBT_PROFILES_DIR = Path("/dbt/profiles")


class CustomDbtTranslator(DagsterDbtTranslator):
    def get_asset_key(self, dbt_resource_props):
        return AssetKey(dbt_resource_props["name"])

    def get_group_name(self, dbt_resource_props):
        model_name = dbt_resource_props["name"]
        if model_name.startswith("stg_"):
            return "staging"
        if model_name.startswith("int_"):
            return "intermediate"
        if model_name.startswith(("fct_", "fact_", "dim_", "mart_", "mar_")):
            return "marts"
        return "transform"

    def get_source_asset_key(self, dbt_source_props):
        source_name = dbt_source_props["source_name"]
        table_name = dbt_source_props["name"]
        if source_name == "dagster_assets":
            return AssetKey([table_name])
        return super().get_source_asset_key(dbt_source_props)


@dbt_assets(
    manifest=DBT_PROJECT_DIR / "target" / "manifest.json",
    dagster_dbt_translator=CustomDbtTranslator(),
)
def all_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    """Materialise all dbt models and build docs artifacts."""
    target = context.op_config.get("target") if context.op_config else None
    target = target or "duckdb"

    build_args = [
        "build",
        "--project-dir",
        str(DBT_PROJECT_DIR),
        "--profiles-dir",
        str(DBT_PROFILES_DIR),
        "--target",
        target,
    ]

    build_invocation = dbt.cli(build_args, context=context)
    yield from build_invocation.stream()
    build_invocation.wait()

    docs_args = [
        "docs",
        "generate",
        "--project-dir",
        str(DBT_PROJECT_DIR),
        "--profiles-dir",
        str(DBT_PROFILES_DIR),
        "--target",
        target,
    ]
    dbt.cli(docs_args, context=context).wait()
