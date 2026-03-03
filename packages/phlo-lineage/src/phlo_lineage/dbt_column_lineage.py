"""Extract column-level lineage from dbt manifest.json.

Uses same-name intersection heuristics — not full SQL parsing.
Each mapping is tagged with source_type="dbt_heuristic" to signal this.

Example:
    >>> import json
    >>> manifest = json.load(open("target/manifest.json"))
    >>> mappings = extract_column_lineage(manifest)
"""

from __future__ import annotations

from typing import Any

from phlo.logging import get_logger
from phlo_lineage.store import ColumnLineage

logger = get_logger(__name__)


def _resolve_asset_name(node: dict[str, Any]) -> str:
    """Derive a qualified asset name from a dbt node.

    Uses ``schema.alias`` when available, falling back to ``schema.name``.
    """
    schema = node.get("schema", "")
    name = node.get("alias") or node.get("name", "")
    return f"{schema}.{name}" if schema else name


def _get_node_columns(node: dict[str, Any]) -> set[str]:
    """Return the set of column names defined on a dbt node."""
    columns: dict[str, Any] = node.get("columns", {})
    return set(columns.keys())


def extract_column_lineage(manifest: dict[str, Any]) -> list[ColumnLineage]:
    """Extract column lineage from a dbt manifest using same-name heuristics.

    For each dbt model node:
    - Determine ``target_asset`` from node schema + alias/name.
    - Collect ``target_columns`` from ``node["columns"]``.
    - For each upstream node in ``depends_on["nodes"]``:
        - Collect upstream columns.
        - Create a ``ColumnLineage`` mapping for every column name that
          appears in **both** the upstream and downstream node.

    This is a heuristic: columns that share a name across an edge are
    assumed to carry lineage.  The ``source_type`` field is set to
    ``"dbt_heuristic"`` to make this explicit.

    Args:
        manifest: Parsed dbt ``manifest.json`` dict.

    Returns:
        List of ``ColumnLineage`` mappings.
    """
    nodes: dict[str, Any] = manifest.get("nodes", {})
    mappings: list[ColumnLineage] = []

    model_nodes = {key: node for key, node in nodes.items() if node.get("resource_type") == "model"}

    logger.info(
        "column_lineage_extraction_started",
        model_count=len(model_nodes),
    )

    for node_key, node in model_nodes.items():
        target_asset = _resolve_asset_name(node)
        target_columns = _get_node_columns(node)

        if not target_columns:
            logger.debug(
                "column_lineage_no_columns",
                node_key=node_key,
                target_asset=target_asset,
            )
            continue

        upstream_keys: list[str] = node.get("depends_on", {}).get("nodes", [])

        for upstream_key in upstream_keys:
            upstream_node = nodes.get(upstream_key)
            if upstream_node is None:
                continue

            source_asset = _resolve_asset_name(upstream_node)
            source_columns = _get_node_columns(upstream_node)

            shared = target_columns & source_columns
            for col in sorted(shared):
                mappings.append(
                    ColumnLineage(
                        source_asset=source_asset,
                        source_column=col,
                        target_asset=target_asset,
                        target_column=col,
                        source_type="dbt_heuristic",
                    )
                )

    logger.info(
        "column_lineage_extraction_completed",
        mapping_count=len(mappings),
    )
    return mappings
