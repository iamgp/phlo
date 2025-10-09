import os
from pathlib import Path
from dagster import AssetExecutionContext, AssetKey
from dagster_dbt import DbtCliResource, dbt_assets, DagsterDbtTranslator

DBT_PROJECT_DIR = Path("/dbt")
DBT_PROFILES_DIR = Path("/dbt/profiles")


class CustomDbtTranslator(DagsterDbtTranslator):
    def get_asset_key(self, dbt_resource_props):
        return AssetKey(dbt_resource_props["name"])

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
    select="stg_nightscout_glucose",
    dagster_dbt_translator=CustomDbtTranslator(),
)
def dbt_nightscout_staging(context: AssetExecutionContext, dbt: DbtCliResource):
    """Nightscout staging models"""
    yield from dbt.cli(["run", "--select", "stg_nightscout_glucose"], context=context).stream()


@dbt_assets(
    manifest=DBT_PROJECT_DIR / "target" / "manifest.json",
    select="stg_bioreactor",
    dagster_dbt_translator=CustomDbtTranslator(),
)
def dbt_bioreactor_staging(context: AssetExecutionContext, dbt: DbtCliResource):
    """Bioreactor staging models"""
    yield from dbt.cli(["run", "--select", "stg_bioreactor"], context=context).stream()


@dbt_assets(
    manifest=DBT_PROJECT_DIR / "target" / "manifest.json",
    select="tag:int tag:curated",
    dagster_dbt_translator=CustomDbtTranslator(),
)
def dbt_curated(context: AssetExecutionContext, dbt: DbtCliResource):
    """Curated layer models"""
    yield from dbt.cli(["run", "--select", "tag:int", "tag:curated"], context=context).stream()


@dbt_assets(
    manifest=DBT_PROJECT_DIR / "target" / "manifest.json",
    select="tag:mart",
    dagster_dbt_translator=CustomDbtTranslator(),
)
def dbt_postgres_marts(context: AssetExecutionContext, dbt: DbtCliResource):
    """Postgres marts"""
    yield from dbt.cli(["run", "--select", "tag:mart", "--target", "postgres"], context=context).stream()
