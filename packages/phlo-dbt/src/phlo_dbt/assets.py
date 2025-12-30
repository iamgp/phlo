from __future__ import annotations

import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

import dagster as dg
from dagster import AssetKey
from dagster_dbt import DbtCliResource, dbt_assets
from phlo.config import get_settings
from phlo.hooks import (
    LineageEventEmitter,
)
from phlo_dagster.partitions import daily_partition

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


def _selected_model_names(context: Any) -> list[str]:
    names: list[str] = []
    if hasattr(context, "selected_output_names"):
        names = [str(name) for name in context.selected_output_names]
    elif hasattr(context, "selected_asset_keys"):
        names = [
            "/".join(key.path) if hasattr(key, "path") else str(key)
            for key in context.selected_asset_keys
        ]
    return names


def _asset_key_to_str(asset_key: AssetKey) -> str:
    if hasattr(asset_key, "path") and asset_key.path:
        return "/".join(str(part) for part in asset_key.path)
    return str(asset_key)


def _emit_dbt_lineage(
    manifest_path: Path,
    translator: CustomDbtTranslator,
    *,
    lineage_emitter: LineageEventEmitter,
    logger: Any,
    reader: Callable[[str], Any],
) -> None:
    if not manifest_path.exists():
        logger.warning("dbt manifest not found at %s; skipping lineage emit", manifest_path)
        return
    try:
        manifest = reader(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("Failed to read dbt manifest for lineage: %s", exc)
        return
    if not isinstance(manifest, Mapping):
        logger.warning("dbt manifest payload is not a mapping; skipping lineage emit")
        return

    nodes = manifest.get("nodes") or {}
    sources = manifest.get("sources") or {}
    if not isinstance(nodes, Mapping) or not isinstance(sources, Mapping):
        logger.warning("dbt manifest nodes or sources missing; skipping lineage emit")
        return

    asset_keys: dict[str, str] = {}
    for unique_id, props in {**nodes, **sources}.items():
        if not isinstance(props, Mapping):
            continue
        try:
            asset_key = translator.get_asset_key(props)
        except Exception:
            continue
        asset_keys[str(unique_id)] = _asset_key_to_str(asset_key)

    edges: list[tuple[str, str]] = []
    target_keys: list[str] = []
    for unique_id, props in nodes.items():
        if not isinstance(props, Mapping):
            continue
        resource_type = str(props.get("resource_type") or "")
        if resource_type not in {"model", "seed", "snapshot"}:
            continue
        target_key = asset_keys.get(str(unique_id))
        if not target_key:
            continue
        depends_on = props.get("depends_on") or {}
        depends_nodes = depends_on.get("nodes") or []
        if not isinstance(depends_nodes, list):
            continue
        for upstream_id in depends_nodes:
            source_key = asset_keys.get(str(upstream_id))
            if source_key:
                edges.append((source_key, target_key))
        target_keys.append(target_key)

    if edges:
        lineage_emitter.emit_edges(
            edges=edges,
            asset_keys=sorted(set(target_keys)),
            metadata={"source": "dbt", "manifest_path": str(manifest_path)},
        )


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
        """
        Dagster asset definition that delegates to DbtTransformer.

        Uses dagster-dbt's DbtCliResource for streaming output, but core logic
        is orchestrator-agnostic via DbtTransformer.
        """
        import os

        target = context.op_config.get("target") if context.op_config else None
        target = target or "dev"
        partition_date = context.partition_key if context.has_partition_key else None

        os.environ.setdefault("TRINO_HOST", settings.trino_host)
        os.environ.setdefault("TRINO_PORT", str(settings.trino_port))

        # Use DbtTransformer for core logic (events, lineage)
        from phlo_dbt.transformer import DbtTransformer

        transformer = DbtTransformer(
            context=context,
            logger=context.log,
            project_dir=dbt_project_path,
            profiles_dir=dbt_profiles_path,
            target=target,
        )

        # For Dagster, we still use dbt.cli for streaming output to the UI
        # But the transformer handles event emission and lineage
        build_args = [
            "build",
            "--project-dir",
            str(dbt_project_path),
            "--profiles-dir",
            str(settings.dbt_profiles_path),
            "--target",
            target,
        ]

        if partition_date:
            build_args.extend(["--vars", f'{{"partition_date_str": "{partition_date}"}}'])
            context.log.info(f"Running dbt for partition: {partition_date}")

        # Run via dagster-dbt for streaming
        try:
            build_invocation = dbt.cli(build_args, context=context)
            yield from build_invocation.stream().fetch_column_metadata()
            build_invocation.wait()
        except Exception as exc:
            # Emit failure events via transformer's event emitters
            # (transformer.run_transform would do this, but we ran via dbt.cli)
            context.log.error(f"dbt build failed: {exc}")
            raise

        # Run transformer for docs and lineage (events already emitted by dbt.cli success)
        # We call a subset of transformer logic for post-processing
        transformer.run_transform(
            partition_key=partition_date,
            parameters={"generate_docs": True, "skip_build": True},  # We already built
        )

        # Dagster-specific: copy artifacts to default target
        default_target_dir = dbt_project_path / "target"
        default_target_dir.mkdir(parents=True, exist_ok=True)

    resources: dict[str, Any] = {
        "dbt": DbtCliResource(
            project_dir=str(dbt_project_path),
            profiles_dir=str(dbt_profiles_path),
        )
    }

    return dg.Definitions(assets=[all_dbt_assets], resources=resources)
