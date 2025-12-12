# dbt.py - Dagster dbt asset definitions and custom translator for data transformations
# Integrates dbt models into Dagster assets with custom grouping and partitioning

from __future__ import annotations

import os
import shutil
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

    def get_description(self, dbt_resource_props: Mapping[str, Any]) -> str | None:
        """Get description including compiled SQL for Observatory lineage parsing.

        The compiled SQL is essential for the Observatory's Query Source Data feature
        to correctly parse column mappings and build WHERE clauses for upstream queries.
        Reads directly from target/compiled/ files which contain fully resolved SQL.
        """
        import logging

        logger = logging.getLogger(__name__)
        model_name = dbt_resource_props.get("name", "")

        # Get the docstring description if available
        docstring = dbt_resource_props.get("description", "")

        # Try to read compiled SQL from file (most reliable source)
        compiled_sql = ""
        compiled_path = dbt_resource_props.get("compiled_path")
        logger.info(f"[CustomDbtTranslator] Model: {model_name}, compiled_path: {compiled_path}")

        if compiled_path:
            try:
                compiled_file = DBT_PROJECT_DIR / compiled_path
                logger.info(
                    f"[CustomDbtTranslator] full path: {compiled_file}, exists: {compiled_file.exists()}"
                )
                if compiled_file.exists():
                    compiled_sql = compiled_file.read_text()
                    logger.info(
                        f"[CustomDbtTranslator] Read compiled SQL, length: {len(compiled_sql)}"
                    )
            except Exception as e:
                logger.warning(f"[CustomDbtTranslator] Failed to read compiled file: {e}")

        # Fallback to manifest compiled_code or raw_code
        if not compiled_sql:
            compiled_sql = dbt_resource_props.get("compiled_code") or dbt_resource_props.get(
                "raw_code", ""
            )
            logger.info(f"[CustomDbtTranslator] Using fallback, length: {len(compiled_sql)}")

        # Build description with model name header and SQL
        parts = [f"dbt model {model_name}"]
        if docstring:
            parts.append(docstring)
        if compiled_sql:
            parts.append("\n#### Raw SQL:\n```sql\n" + compiled_sql + "\n```")

        return "\n\n".join(parts)

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

    def get_kinds(self, dbt_resource_props: Mapping[str, Any]) -> set[str]:
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

    # Inject _phlo_row_id to all materialized tables for lineage tracking
    try:
        import json

        import trino

        from phlo.lineage.dbt_inject import inject_row_ids_for_dbt_run

        run_results_path = default_target_dir / "run_results.json"
        if run_results_path.exists():
            with open(run_results_path) as f:
                run_results = json.load(f)

            trino_conn = trino.dbapi.connect(
                host=config.trino_host,
                port=config.trino_port,
                user="dagster",
                catalog="iceberg",
            )

            context.log.info("[dbt] Injecting _phlo_row_id to materialized tables...")
            injection_results = inject_row_ids_for_dbt_run(
                trino_connection=trino_conn,
                run_results=run_results,
                catalog="iceberg",
                context=context,
            )
            context.log.info(f"[dbt] Row ID injection results: {injection_results}")
            trino_conn.close()
    except Exception as e:
        context.log.warning(f"[dbt] Row ID injection failed (non-fatal): {e}")


def build_defs():
    """Build dbt transform definitions."""
    import dagster as dg

    return dg.Definitions(assets=[all_dbt_assets])
