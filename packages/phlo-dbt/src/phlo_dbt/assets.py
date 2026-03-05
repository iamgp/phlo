from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from phlo.capabilities import (
    AssetSpec,
    MaterializeResult,
    PartitionSpec,
    RunSpec,
    routing_from_context,
)
from phlo.capabilities.runtime import RuntimeContext
from phlo.logging import get_logger
from phlo_dbt.settings import get_settings

from phlo_dbt.transformer import DbtTransformer, ensure_dbt_manifest
from phlo_dbt.translator import DbtSpecTranslator

logger = get_logger(__name__)


def _target_from_runtime(runtime: RuntimeContext) -> str:
    """Resolve dbt target from canonical runtime routing with legacy fallback."""
    routing = routing_from_context(runtime)
    if routing.environment:
        return routing.environment

    runtime_tags = getattr(runtime, "tags", {}) or {}
    if isinstance(runtime_tags, Mapping):
        legacy_target = runtime_tags.get("dbt_target")
        if isinstance(legacy_target, str) and legacy_target:
            return legacy_target

    return "dev"


def _asset_deps(unique_id: str, nodes: Mapping[str, Any], asset_keys: dict[str, str]) -> list[str]:
    """Resolve upstream asset dependencies for a dbt node.

    Args:
        unique_id: dbt unique node identifier.
        nodes: Manifest node mapping.
        asset_keys: Mapping of dbt unique IDs to asset keys.

    Returns:
        Upstream asset keys for the node.
    """
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
    """Execute a single dbt model and map result to materialization output.

    Args:
        model_name: dbt model name to execute.
        project_dir: dbt project root.
        profiles_dir: dbt profiles directory.
        runtime: Asset runtime context.

    Returns:
        Materialization results for the model run.
    """
    target = _target_from_runtime(runtime)
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
    """Build asset specifications from dbt manifest metadata.

    Returns:
        Asset specs representing supported dbt nodes.
    """
    settings = get_settings()

    dbt_project_path = settings.dbt_project_path
    dbt_profiles_path = settings.dbt_profiles_path
    manifest_path = dbt_project_path / "target" / "manifest.json"

    if not dbt_project_path.exists():
        logger.info(
            "dbt_asset_specs_skipped_project_missing",
            dbt_project_path=str(dbt_project_path),
        )
        return []

    if not ensure_dbt_manifest(dbt_project_path, dbt_profiles_path):
        logger.warning(
            "dbt_asset_specs_skipped_manifest_unavailable",
            dbt_project_path=str(dbt_project_path),
            profiles_path=str(dbt_profiles_path),
        )
        return []

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.warning(
            "dbt_asset_specs_manifest_read_failed",
            manifest_path=str(manifest_path),
        )
        return []

    if not isinstance(manifest, Mapping):
        logger.warning(
            "dbt_asset_specs_manifest_not_mapping",
            manifest_path=str(manifest_path),
        )
        return []

    translator = DbtSpecTranslator()
    nodes = manifest.get("nodes") or {}
    sources = manifest.get("sources") or {}
    if not isinstance(nodes, Mapping) or not isinstance(sources, Mapping):
        logger.warning(
            "dbt_asset_specs_manifest_shape_invalid",
            manifest_path=str(manifest_path),
        )
        return []

    asset_keys: dict[str, str] = {}
    for unique_id, props in {**nodes, **sources}.items():
        if not isinstance(props, Mapping):
            continue
        try:
            asset_key = translator.get_asset_key(props)
        except Exception:
            logger.exception(
                "dbt_asset_specs_asset_key_translate_failed",
                unique_id=str(unique_id),
            )
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
            """Execute one dbt-backed asset run.

            Args:
                runtime: Asset runtime context.
                model: Bound dbt model name for this spec.

            Returns:
                Materialization results for the selected dbt model.
            """
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

    logger.info(
        "dbt_asset_specs_built",
        spec_count=len(specs),
        dbt_project_path=str(dbt_project_path),
    )
    return specs
