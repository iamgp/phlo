from pathlib import Path
from dagster import AssetExecutionContext, AssetKey
from dagster_dbt import DbtCliResource, dbt_assets, DagsterDbtTranslator

DBT_PROJECT_DIR = Path("/dbt")
DBT_PROFILES_DIR = Path("/dbt/profiles")


class CustomDbtTranslator(DagsterDbtTranslator):
    def get_asset_key(self, dbt_resource_props):
        return AssetKey(dbt_resource_props["name"])

    def get_group_name(self, dbt_resource_props):
        """Assign dbt models to groups based on their layer"""
        model_name = dbt_resource_props["name"]

        if model_name.startswith("stg_"):
            return "staging"
        elif model_name.startswith("int_"):
            return "intermediate"
        elif model_name.startswith(("fct_", "fact_", "dim_", "mart_", "mar_")):
            return "marts"
        else:
            return "transform"

    def get_source_asset_key(self, dbt_source_props):
        """Map dbt sources to Dagster asset keys"""
        source_name = dbt_source_props["source_name"]
        table_name = dbt_source_props["name"]

        # Map our dagster_assets source tables to actual asset keys
        if source_name == "dagster_assets":
            return AssetKey([table_name])

        return super().get_source_asset_key(dbt_source_props)


@dbt_assets(
    manifest=DBT_PROJECT_DIR / "target" / "manifest.json",
    dagster_dbt_translator=CustomDbtTranslator(),
)
def all_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    """All dbt models - automatically discovers models from manifest"""
    yield from dbt.cli(["build"], context=context).stream()
