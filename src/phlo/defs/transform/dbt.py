# dbt.py - Dagster dbt asset definitions and custom translator for data transformations
# Integrates dbt models into Dagster assets with custom grouping and partitioning

from __future__ import annotations

import logging
import os
import shutil
from collections.abc import Generator

from dagster_dbt import DbtCliResource, dbt_assets

from phlo.config import config
from phlo.defs.partitions import daily_partition
from phlo.defs.transform.dbt_translator import CustomDbtTranslator

# --- Configuration ---
DBT_PROJECT_DIR = config.dbt_project_path
DBT_PROFILES_DIR = config.dbt_profiles_path

logger = logging.getLogger(__name__)


def build_all_dbt_assets(*, manifest_path) -> object:
    @dbt_assets(
        manifest=manifest_path,
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

    return all_dbt_assets


def build_defs():
    """Build dbt transform definitions."""
    import dagster as dg

    manifest_path = DBT_PROJECT_DIR / "target" / "manifest.json"
    if not manifest_path.exists():
        logger.debug("No dbt manifest at %s; skipping dbt asset definitions", manifest_path)
        return dg.Definitions(assets=[])

    return dg.Definitions(assets=[build_all_dbt_assets(manifest_path=manifest_path)])
