from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import dagster as dg
from dagster_dbt import DbtCliResource, dbt_assets
from phlo.config import get_settings
from phlo.dagster.partitions import daily_partition

from phlo_dbt.translator import CustomDbtTranslator


def _latest_project_mtime(dbt_project_path: Path) -> float:
    candidates: list[Path] = [
        dbt_project_path / "dbt_project.yml",
        dbt_project_path / "packages.yml",
        dbt_project_path / "package-lock.yml",
    ]
    candidate_dirs = [
        dbt_project_path / "models",
        dbt_project_path / "macros",
        dbt_project_path / "seeds",
        dbt_project_path / "snapshots",
        dbt_project_path / "tests",
        dbt_project_path / "analysis",
    ]

    latest = 0.0
    for path in candidates:
        if path.exists():
            latest = max(latest, path.stat().st_mtime)

    for directory in candidate_dirs:
        if not directory.exists():
            continue
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                latest = max(latest, file_path.stat().st_mtime)

    return latest


def ensure_dbt_manifest(dbt_project_path: Path, profiles_path: Path) -> bool:
    manifest_path = dbt_project_path / "target" / "manifest.json"

    needs_compile = not manifest_path.exists()
    if not needs_compile:
        try:
            needs_compile = _latest_project_mtime(dbt_project_path) > manifest_path.stat().st_mtime
        except OSError:
            needs_compile = True

    if not needs_compile:
        return True

    try:
        result = subprocess.run(
            ["dbt", "compile", "--profiles-dir", str(profiles_path)],
            cwd=str(dbt_project_path),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        return False

    return result.returncode == 0 and manifest_path.exists()


def build_dbt_definitions() -> dg.Definitions:
    settings = get_settings()

    dbt_project_path = settings.dbt_project_path
    dbt_profiles_path = settings.dbt_profiles_path
    manifest_path = dbt_project_path / "target" / "manifest.json"

    if not dbt_project_path.exists():
        return dg.Definitions()

    if not ensure_dbt_manifest(dbt_project_path, dbt_profiles_path):
        return dg.Definitions()

    translator = CustomDbtTranslator()

    @dbt_assets(
        manifest=manifest_path,
        dagster_dbt_translator=translator,
        partitions_def=daily_partition,
    )
    def all_dbt_assets(context, dbt: DbtCliResource):  # type: ignore[valid-type]
        import os
        import shutil

        target = context.op_config.get("target") if context.op_config else None
        target = target or "dev"

        build_args = [
            "build",
            "--project-dir",
            str(dbt_project_path),
            "--profiles-dir",
            str(settings.dbt_profiles_path),
            "--target",
            target,
        ]

        if context.has_partition_key:
            partition_date = context.partition_key
            build_args.extend(["--vars", f'{{\"partition_date_str\": \"{partition_date}\"}}'])
            context.log.info(f"Running dbt for partition: {partition_date}")

        os.environ.setdefault("TRINO_HOST", settings.trino_host)
        os.environ.setdefault("TRINO_PORT", str(settings.trino_port))

        build_invocation = dbt.cli(build_args, context=context)
        yield from build_invocation.stream().fetch_column_metadata()
        build_invocation.wait()

        docs_args = [
            "docs",
            "generate",
            "--project-dir",
            str(dbt_project_path),
            "--profiles-dir",
            str(settings.dbt_profiles_path),
            "--target",
            target,
        ]
        docs_invocation = dbt.cli(docs_args, context=context).wait()

        default_target_dir = dbt_project_path / "target"
        default_target_dir.mkdir(parents=True, exist_ok=True)

        for artifact in ("manifest.json", "catalog.json", "run_results.json"):
            artifact_path = docs_invocation.target_path / artifact
            if artifact_path.exists():
                shutil.copy(artifact_path, default_target_dir / artifact)

    resources: dict[str, Any] = {
        "dbt": DbtCliResource(
            project_dir=str(dbt_project_path),
            profiles_dir=str(dbt_profiles_path),
        )
    }

    return dg.Definitions(assets=[all_dbt_assets], resources=resources)
