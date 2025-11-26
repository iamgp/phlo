# dbt.py - Dagster dbt asset definitions and custom translator for data transformations
# Integrates dbt models into Dagster assets with custom grouping and partitioning

from __future__ import annotations

import shutil
import os
from collections.abc import Generator, Mapping
from typing import Any

from dagster import AssetKey
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets

from phlo.config import config
from phlo.defs.partitions import daily_partition

# --- Configuration ---
DBT_PROJECT_DIR = config.dbt_project_path
DBT_PROFILES_DIR = config.dbt_profiles_path


class CustomDbtTranslator(DagsterDbtTranslator):
    """Custom translator for mapping dbt models to Dagster assets."""

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        resource_type = dbt_resource_props.get("resource_type")
        if resource_type == "source":
            source_name = dbt_resource_props["source_name"]
            table_name = dbt_resource_props["name"]
            if source_name == "dagster_assets":
                # Convention: dbt sources map to dlt_<table_name> assets
                return AssetKey([f"dlt_{table_name}"])
            return super().get_asset_key(dbt_resource_props)
        return AssetKey(dbt_resource_props["name"])

    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> str:
        """Derive group from dbt model path or naming convention."""
        model_name = dbt_resource_props["name"]

        # Try to get group from dbt model config/meta
        meta = dbt_resource_props.get("meta", {})
        if "group" in meta:
            return meta["group"]

        # Try to derive from fqn (folder path)
        fqn = dbt_resource_props.get("fqn", [])
        if len(fqn) > 2:
            # fqn is like ['project', 'folder', 'model']
            folder = fqn[1]
            if folder in ("bronze", "silver", "gold", "marts", "staging"):
                # Use folder as group
                return folder

        # Fallback: group by naming convention (layer prefix)
        if model_name.startswith("stg_"):
            return "bronze"
        if model_name.startswith(("dim_", "fct_")):
            return "silver"
        if model_name.startswith("mrt_"):
            return "gold"
        return "transform"

    def get_kinds(
        self, dbt_resource_props: Mapping[str, Any]
    ) -> set[str]:
        """Return kinds for the asset."""
        return {"dbt", "trino"}


@dbt_assets(
    manifest=DBT_PROJECT_DIR / "target" / "manifest.json",
    dagster_dbt_translator=CustomDbtTranslator(),
    partitions_def=daily_partition,
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


def build_defs():
    """Build dbt transform definitions."""
    import dagster as dg
    return dg.Definitions(assets=[all_dbt_assets])
