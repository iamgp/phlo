"""Helpers for importing dbt manifest lineage into configured Phlo sinks."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from phlo.capabilities.discovery import discover_capabilities
from phlo.capabilities.resolver import resolve_capability
from phlo.logging import get_logger
from phlo_dbt.translator import DbtSpecTranslator

logger = get_logger(__name__)


def load_dbt_manifest(manifest_path: Path) -> dict[str, Any] | None:
    """Return a parsed dbt manifest payload when available."""
    if not manifest_path.exists():
        logger.info("dbt_lineage_manifest_missing", manifest_path=str(manifest_path))
        return None

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.warning(
            "dbt_lineage_manifest_read_failed",
            manifest_path=str(manifest_path),
            exc_info=True,
        )
        return None

    if not isinstance(manifest, dict):
        logger.warning(
            "dbt_lineage_manifest_invalid",
            manifest_path=str(manifest_path),
            manifest_type=type(manifest).__name__,
        )
        return None

    return manifest


def collect_asset_lineage(
    manifest: Mapping[str, Any],
    *,
    translator: DbtSpecTranslator | None = None,
) -> tuple[list[tuple[str, str]], list[str]]:
    """Collect asset-level lineage edges and asset keys from a dbt manifest."""
    nodes = manifest.get("nodes") or {}
    sources = manifest.get("sources") or {}
    if not isinstance(nodes, Mapping) or not isinstance(sources, Mapping):
        return [], []

    translator = translator or DbtSpecTranslator()
    asset_keys: dict[str, str] = {}
    for unique_id, props in {**nodes, **sources}.items():
        if not isinstance(props, Mapping):
            continue
        try:
            asset_key = translator.get_asset_key(props)
        except Exception:
            logger.debug(
                "dbt_lineage_asset_key_skipped",
                unique_id=str(unique_id),
                exc_info=True,
            )
            continue
        asset_keys[str(unique_id)] = str(asset_key)

    edges: list[tuple[str, str]] = []
    target_keys: set[str] = set()
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
        target_keys.add(target_key)

    return edges, sorted(target_keys)


def import_manifest_lineage(manifest_path: Path) -> dict[str, int]:
    """Import asset lineage and best-effort column lineage from a dbt manifest."""
    manifest = load_dbt_manifest(manifest_path)
    if manifest is None:
        return {"asset_edges": 0, "column_mappings": 0}

    discover_capabilities()
    resolution = resolve_capability("lineage_sink")
    if resolution is None:
        logger.info(
            "dbt_lineage_import_skipped_no_sink",
            manifest_path=str(manifest_path),
        )
        return {"asset_edges": 0, "column_mappings": 0}

    edges, asset_keys = collect_asset_lineage(manifest)
    if edges or asset_keys:
        resolution.provider.record_asset_edges(
            edges,
            asset_keys=asset_keys,
            metadata={"source": "dbt", "manifest_path": str(manifest_path)},
            tags={"tool": "dbt"},
        )

    column_mappings = 0
    try:
        from phlo_lineage.dbt_column_lineage import extract_column_lineage
        from phlo_lineage.store import LineageStore, resolve_lineage_db_url_with_postgres_fallback
    except ImportError:
        logger.debug(
            "dbt_column_lineage_import_unavailable",
            manifest_path=str(manifest_path),
        )
    else:
        connection_string = resolve_lineage_db_url_with_postgres_fallback()
        if connection_string:
            mappings = extract_column_lineage(manifest)
            if mappings:
                column_mappings = LineageStore(connection_string).record_column_lineage(mappings)

    logger.info(
        "dbt_lineage_import_completed",
        manifest_path=str(manifest_path),
        asset_edge_count=len(edges),
        asset_key_count=len(asset_keys),
        column_mapping_count=column_mappings,
        lineage_sink_name=resolution.name,
    )
    return {"asset_edges": len(edges), "column_mappings": column_mappings}
