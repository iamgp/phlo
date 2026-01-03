from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from phlo.capabilities import AssetSpec, MaterializeResult, PartitionSpec, RunSpec
from phlo.capabilities.runtime import RuntimeContext
from phlo.config import get_settings

from phlo_dbt.transformer import DbtTransformer
from phlo_dbt.translator import DbtSpecTranslator


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
        try:
            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            needs_compile = True
        else:
            if not isinstance(manifest_payload, Mapping):
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

    if result.returncode != 0 or not manifest_path.exists():
        return False

    try:
        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False

    return isinstance(manifest_payload, Mapping)


def _asset_deps(unique_id: str, nodes: Mapping[str, Any], asset_keys: dict[str, str]) -> list[str]:
    props = nodes.get(unique_id, {})
    depends_on = props.get("depends_on") or {}
    depends_nodes = depends_on.get("nodes") or []
    deps: list[str] = []
    if isinstance(depends_nodes, list):
        for upstream_id in depends_nodes:
            key = asset_keys.get(str(upstream_id))
            if key:
                deps.append(key)
    return deps


def _run_dbt_model(
    *,
    model_name: str,
    project_dir: Path,
    profiles_dir: Path,
    runtime: RuntimeContext,
) -> list[MaterializeResult]:
    target = runtime.tags.get("dbt_target") if runtime.tags else None
    target = target or "dev"
    partition_key = runtime.partition_key

    transformer = DbtTransformer(
        context=runtime,
        logger=runtime.logger,
        project_dir=project_dir,
        profiles_dir=profiles_dir,
        target=target,
    )

    result = transformer.run_transform(
        partition_key=partition_key,
        parameters={"select": [model_name]},
    )

    return [
        MaterializeResult(
            status=result.status,
            metadata={
                "model": model_name,
                "dbt_target": target,
                "dbt_status": result.status,
                "dbt_metadata": result.metadata,
            },
        )
    ]


def build_dbt_asset_specs() -> list[AssetSpec]:
    settings = get_settings()

    dbt_project_path = settings.dbt_project_path
    dbt_profiles_path = settings.dbt_profiles_path
    manifest_path = dbt_project_path / "target" / "manifest.json"

    if not dbt_project_path.exists():
        return []

    if not ensure_dbt_manifest(dbt_project_path, dbt_profiles_path):
        return []

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []

    if not isinstance(manifest, Mapping):
        return []

    translator = DbtSpecTranslator()
    nodes = manifest.get("nodes") or {}
    sources = manifest.get("sources") or {}
    if not isinstance(nodes, Mapping) or not isinstance(sources, Mapping):
        return []

    asset_keys: dict[str, str] = {}
    for unique_id, props in {**nodes, **sources}.items():
        if not isinstance(props, Mapping):
            continue
        try:
            asset_key = translator.get_asset_key(props)
        except Exception:
            continue
        asset_keys[str(unique_id)] = str(asset_key)

    specs: list[AssetSpec] = []
    for unique_id, props in nodes.items():
        if not isinstance(props, Mapping):
            continue
        resource_type = str(props.get("resource_type") or "")
        if resource_type not in {"model", "seed", "snapshot"}:
            continue
        asset_key = asset_keys.get(str(unique_id))
        if not asset_key:
            continue
        model_name = str(props.get("name") or asset_key)
        deps = _asset_deps(str(unique_id), nodes, asset_keys)
        description = translator.get_description(props)
        group = translator.get_group_name(props)
        kinds = translator.get_kinds(props)
        metadata = translator.get_metadata(props)
        tags = {"tool": "dbt"}

        def _runner(runtime: RuntimeContext, model=model_name) -> list[MaterializeResult]:
            return _run_dbt_model(
                model_name=model,
                project_dir=dbt_project_path,
                profiles_dir=dbt_profiles_path,
                runtime=runtime,
            )

        specs.append(
            AssetSpec(
                key=asset_key,
                group=group,
                description=description,
                kinds=kinds,
                tags=tags,
                metadata=metadata,
                partitions=PartitionSpec(kind="daily"),
                deps=deps,
                run=RunSpec(fn=_runner),
            )
        )

    return specs
