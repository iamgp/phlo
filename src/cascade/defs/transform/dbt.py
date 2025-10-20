# dbt.py - Dagster dbt asset definitions and custom translator for data transformations
# Integrates dbt models into Dagster assets with custom grouping and partitioning
# handles the bronze, silver, and gold layer transformations

from __future__ import annotations

import shutil
import os
from collections.abc import Generator, Mapping
from typing import Any

from dagster import AssetKey
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets

from cascade.config import config
from cascade.defs.partitions import daily_partition

# --- Configuration ---
# dbt project and profiles directory paths
DBT_PROJECT_DIR = config.dbt_project_path
DBT_PROFILES_DIR = config.dbt_profiles_path


# --- Custom DBT Translator ---
# Custom translator for mapping dbt models to Dagster assets with proper grouping
class CustomDbtTranslator(DagsterDbtTranslator):
    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        return AssetKey(dbt_resource_props["name"])

    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> str:
        model_name = dbt_resource_props["name"]
        if model_name.startswith("stg_"):
            return "bronze"
        if model_name.startswith(("dim_", "fct_")):
            return "silver"
        if model_name.startswith("mrt_"):
            return "gold"
        return "transform"

    def get_source_asset_key(self, dbt_source_props: Mapping[str, Any]) -> AssetKey:
        source_name = dbt_source_props["source_name"]
        table_name = dbt_source_props["name"]
        if source_name == "dagster_assets":
            return AssetKey([table_name])
        return super().get_source_asset_key(dbt_source_props)


# --- DBT Assets Definition ---
# Main dbt assets function that executes dbt build and generates documentation
@dbt_assets(
    manifest=DBT_PROJECT_DIR / "target" / "manifest.json",
    dagster_dbt_translator=CustomDbtTranslator(),
)
def all_dbt_assets(context, dbt: DbtCliResource) -> Generator[object, None, None]:
    target = context.op_config.get("target") if context.op_config else None
    target = target or "dev"

    build_args = [
    "build",
    "--project-dir",
    str(DBT_PROJECT_DIR),
    "--profiles-dir",
    str(DBT_PROFILES_DIR),
    "--target",
    target,
    ]

    # Pass partition date to dbt as a variable for incremental processing
    if context.has_partition_key:
        partition_date = context.partition_key
        build_args.extend(["--vars", f'{{"partition_date_str": "{partition_date}"}}'])
        context.log.info(f"Running dbt for partition: {partition_date}")

    os.environ.setdefault("TRINO_HOST", config.trino_host)
    os.environ.setdefault("TRINO_PORT", str(config.trino_port))

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
    docs_invocation = dbt.cli(docs_args, context=context).wait()

    default_target_dir = DBT_PROJECT_DIR / "target"
    default_target_dir.mkdir(parents=True, exist_ok=True)

    for artifact in ("manifest.json", "catalog.json", "run_results.json"):
        artifact_path = docs_invocation.target_path / artifact
        if artifact_path.exists():
            shutil.copy(artifact_path, default_target_dir / artifact)
