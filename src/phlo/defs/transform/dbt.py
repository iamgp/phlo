# dbt.py - Dagster dbt asset definitions and custom translator for data transformations
# Integrates dbt models into Dagster assets with custom grouping and partitioning

from __future__ import annotations

import json
import logging
import os
import shutil
from collections.abc import Generator

import dagster as dg
from dagster_dbt import DbtCliResource, dbt_assets

from phlo.config import config
from phlo.defs.partitions import daily_partition
from phlo.defs.transform.dbt_translator import CustomDbtTranslator
from phlo.lineage.dbt_inject import inject_row_ids_for_dbt_run
from phlo.quality.dbt_asset_checks import extract_dbt_asset_checks

# --- Configuration ---
DBT_PROJECT_DIR = config.dbt_project_path
DBT_PROFILES_DIR = config.dbt_profiles_path

logger = logging.getLogger(__name__)


def build_all_dbt_assets(*, manifest_path) -> object:
    translator = CustomDbtTranslator()

    @dbt_assets(
        manifest=manifest_path,
        dagster_dbt_translator=translator,
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

        default_target_dir = DBT_PROJECT_DIR / "target"
        default_target_dir.mkdir(parents=True, exist_ok=True)

        build_run_results = build_invocation.target_path / "run_results.json"
        if build_run_results.exists():
            shutil.copy(build_run_results, default_target_dir / "run_results.json")

        # Inject _phlo_row_id into all successfully built dbt tables
        if build_run_results.exists():
            try:
                import trino

                with open(build_run_results) as handle:
                    run_results = json.load(handle)

                trino_conn = trino.dbapi.connect(
                    host=config.trino_host,
                    port=config.trino_port,
                    user="phlo",
                    catalog="iceberg",
                )
                inject_results = inject_row_ids_for_dbt_run(
                    trino_connection=trino_conn,
                    run_results=run_results,
                    context=context,
                )
                trino_conn.close()

                for table_name, result in inject_results.items():
                    if "error" in result:
                        context.log.warning(
                            f"Failed to inject _phlo_row_id into {table_name}: {result['error']}"
                        )
                    elif not result.get("skipped"):
                        context.log.info(
                            f"Injected _phlo_row_id into {table_name}: {result['rows_updated']} rows"
                        )
            except Exception as e:
                context.log.warning(f"Failed to inject _phlo_row_id: {e}")

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

        for artifact in ("manifest.json", "catalog.json"):
            artifact_path = docs_invocation.target_path / artifact
            if artifact_path.exists():
                shutil.copy(artifact_path, default_target_dir / artifact)

        manifest_json = default_target_dir / "manifest.json"
        run_results_json = default_target_dir / "run_results.json"
        if manifest_json.exists() and run_results_json.exists():
            with open(manifest_json) as handle:
                manifest_data = json.load(handle)
            with open(run_results_json) as handle:
                run_results_data = json.load(handle)

            partition_key = context.partition_key if context.has_partition_key else None
            for check in extract_dbt_asset_checks(
                run_results_data,
                manifest_data,
                translator=translator,
                partition_key=partition_key,
            ):
                yield check

    return all_dbt_assets


def build_defs():
    """Build dbt transform definitions."""
    manifest_path = DBT_PROJECT_DIR / "target" / "manifest.json"
    if not manifest_path.exists():
        logger.debug("No dbt manifest at %s; skipping dbt asset definitions", manifest_path)
        return dg.Definitions(assets=[])

    return dg.Definitions(assets=[build_all_dbt_assets(manifest_path=manifest_path)])
