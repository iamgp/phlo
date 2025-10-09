import os
import sys
from contextlib import contextmanager
from pathlib import Path

import openlineage.dbt
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
    target = os.getenv("DBT_TARGET", "duckdb")
    dbt_args = [
        "build",
        "--project-dir",
        str(DBT_PROJECT_DIR),
        "--profiles-dir",
        str(DBT_PROFILES_DIR),
        "--target",
        target,
    ]
    openlineage_env = {
        "OPENLINEAGE_URL": os.getenv("OPENLINEAGE_URL", "http://marquez:5000"),
        "OPENLINEAGE_NAMESPACE": os.getenv("OPENLINEAGE_NAMESPACE", "lakehouse"),
        "DBT_OPENLINEAGE_URL": os.getenv("OPENLINEAGE_URL", "http://marquez:5000"),
        "DBT_OPENLINEAGE_NAMESPACE": os.getenv("OPENLINEAGE_NAMESPACE", "lakehouse"),
        "DBT_PROJECT_DIR": str(DBT_PROJECT_DIR),
        "DBT_PROFILES_DIR": str(DBT_PROFILES_DIR),
    }

    with _temporary_environ(openlineage_env):
        invocation = dbt.cli(dbt_args, context=context)
        yield from invocation.stream()
        invocation.wait()
        _emit_openlineage_events(dbt_args, target)


@contextmanager
def _temporary_environ(overrides: dict[str, str]):
    original = {}
    try:
        for key, value in overrides.items():
            original[key] = os.environ.get(key)
            os.environ[key] = value
        yield
    finally:
        for key in overrides:
            if original[key] is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original[key]


def _emit_openlineage_events(dbt_args: list[str], target: str) -> None:
    """Trigger openlineage-dbt to parse artifacts and emit dataset/job events."""
    argv_backup = sys.argv[:]
    sys.argv = ["openlineage-dbt"] + dbt_args
    try:
        # Reuse openlineage-dbt's artifact processor without rerunning dbt.
        return_code = openlineage.dbt.consume_local_artifacts(
            args=dbt_args,
            target=target,
            project_dir=str(DBT_PROJECT_DIR),
            profile_name=None,
            model_selector=None,
            models=[],
            openlineage_job_name=None,
        )
    finally:
        sys.argv = argv_backup

    if return_code != 0:
        raise RuntimeError("openlineage-dbt failed to emit lineage events for dbt build")
