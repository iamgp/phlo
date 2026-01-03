"""Lineage API Router.

Endpoints for querying the Phlo row-level lineage store.
Used by the Observatory frontend to display row provenance.
"""

from __future__ import annotations

from collections import deque
from typing import Any

import psycopg2
from fastapi import APIRouter, Query
from anyio.to_thread import run_sync
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel

from phlo.config import get_settings
from phlo.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["lineage"])


def get_connection_string() -> str:
    """Get PostgreSQL connection string for lineage store."""
    settings = get_settings()
    if settings.lineage_db_url:
        return settings.lineage_db_url
    raise RuntimeError(
        "Lineage database URL not configured. Set PHLO_LINEAGE_DB_URL (or "
        "DAGSTER_PG_DB_CONNECTION_STRING)."
    )


# --- Pydantic Models ---


class RowLineageInfo(BaseModel):
    row_id: str
    table_name: str
    source_type: str
    parent_row_ids: list[str]
    created_at: str | None = None


class LineageJourney(BaseModel):
    current: RowLineageInfo | None
    ancestors: list[RowLineageInfo]
    descendants: list[RowLineageInfo]


class AssetNode(BaseModel):
    name: str
    asset_type: str | None = None
    status: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None
    tags: dict[str, Any] | None = None


class AssetEdge(BaseModel):
    source: str
    target: str
    metadata: dict[str, Any] | None = None
    tags: dict[str, Any] | None = None


class AssetLineageGraph(BaseModel):
    assets: dict[str, AssetNode]
    edges: dict[str, list[str]]
    edge_details: list[AssetEdge]


# --- Helper Functions ---


def _execute_lineage_query_sync(query: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
    with psycopg2.connect(get_connection_string()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


async def execute_lineage_query(query: str, params: list[Any]) -> list[dict[str, Any]]:
    """Execute a query against the lineage store."""
    return await run_sync(_execute_lineage_query_sync, query, tuple(params))


def row_to_lineage_info(row: dict[str, Any]) -> RowLineageInfo:
    """Convert database row to RowLineageInfo."""
    return RowLineageInfo(
        row_id=row["row_id"],
        table_name=row["table_name"],
        source_type=row["source_type"],
        parent_row_ids=row.get("parent_row_ids") or [],
        created_at=row["created_at"].isoformat() if row.get("created_at") else None,
    )


def _build_asset_graph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[dict[str, AssetNode], dict[str, list[str]], list[AssetEdge]]:
    assets: dict[str, AssetNode] = {}
    edges_map: dict[str, list[str]] = {}

    for node in nodes:
        name = node["asset_key"]
        assets[name] = AssetNode(
            name=name,
            asset_type=node.get("asset_type"),
            status=node.get("status"),
            description=node.get("description"),
            metadata=node.get("metadata"),
            tags=node.get("tags"),
        )

    for edge in edges:
        source = edge["source_asset"]
        target = edge["target_asset"]
        if source not in assets:
            assets[source] = AssetNode(name=source)
        if target not in assets:
            assets[target] = AssetNode(name=target)
        edges_map.setdefault(source, []).append(target)

    edge_details = [
        AssetEdge(
            source=edge["source_asset"],
            target=edge["target_asset"],
            metadata=edge.get("metadata"),
            tags=edge.get("tags"),
        )
        for edge in edges
    ]
    return assets, edges_map, edge_details


def _filter_asset_graph(
    assets: dict[str, AssetNode],
    edges: dict[str, list[str]],
    edge_details: list[AssetEdge],
    *,
    asset_key: str,
    direction: str,
    depth: int | None,
) -> tuple[dict[str, AssetNode], dict[str, list[str]], list[AssetEdge]]:
    reverse_edges: dict[str, list[str]] = {}
    for source, targets in edges.items():
        for target in targets:
            reverse_edges.setdefault(target, []).append(source)

    def _walk(
        start: str,
        adjacency: dict[str, list[str]],
        max_depth: int | None,
    ) -> set[str]:
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(start, 0)])
        while queue:
            current, current_depth = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            if max_depth is not None and current_depth >= max_depth:
                continue
            for neighbor in adjacency.get(current, []):
                if neighbor not in visited:
                    queue.append((neighbor, current_depth + 1))
        visited.discard(start)
        return visited

    upstream = (
        _walk(asset_key, reverse_edges, depth) if direction in {"upstream", "both"} else set()
    )
    downstream = _walk(asset_key, edges, depth) if direction in {"downstream", "both"} else set()

    keep_assets = {asset_key} | upstream | downstream
    filtered_assets = {name: node for name, node in assets.items() if name in keep_assets}
    filtered_edges = {
        source: [target for target in targets if target in keep_assets]
        for source, targets in edges.items()
        if source in keep_assets
    }
    filtered_edge_details = [
        edge for edge in edge_details if edge.source in keep_assets and edge.target in keep_assets
    ]
    return filtered_assets, filtered_edges, filtered_edge_details


# --- API Endpoints ---


@router.get("/rows/{row_id}", response_model=RowLineageInfo | dict)
async def get_row_lineage(row_id: str) -> RowLineageInfo | dict[str, str]:
    """Get lineage info for a single row."""
    try:
        rows = await execute_lineage_query(
            """
            SELECT row_id, table_name, source_type, parent_row_ids, created_at
            FROM phlo.row_lineage
            WHERE row_id = %s
            """,
            [row_id],
        )

        if not rows:
            return {"error": f"Row {row_id} not found in lineage store"}

        return row_to_lineage_info(rows[0])
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.exception("Failed to get row lineage")
        return {"error": str(e)}


@router.get("/rows/{row_id}/ancestors", response_model=list[RowLineageInfo] | dict)
async def get_row_ancestors(
    row_id: str,
    max_depth: int = Query(default=10, le=50),
) -> list[RowLineageInfo] | dict[str, str]:
    """Get all ancestor rows (recursive)."""
    try:
        rows = await execute_lineage_query(
            """
            WITH RECURSIVE ancestors AS (
                SELECT rl.row_id, rl.table_name, rl.source_type,
                       rl.parent_row_ids, rl.created_at, 1 as depth
                FROM phlo.row_lineage rl
                WHERE rl.row_id = ANY(
                    SELECT unnest(parent_row_ids)
                    FROM phlo.row_lineage
                    WHERE row_id = %s
                )

                UNION ALL

                SELECT rl.row_id, rl.table_name, rl.source_type,
                       rl.parent_row_ids, rl.created_at, a.depth + 1
                FROM phlo.row_lineage rl
                INNER JOIN ancestors a ON rl.row_id = ANY(a.parent_row_ids)
                WHERE a.depth < %s
            )
            SELECT DISTINCT row_id, table_name, source_type,
                   parent_row_ids, created_at
            FROM ancestors
            ORDER BY created_at DESC
            """,
            [row_id, max_depth],
        )

        return [row_to_lineage_info(row) for row in rows]
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.exception("Failed to get row ancestors")
        return {"error": str(e)}


@router.get("/rows/{row_id}/descendants", response_model=list[RowLineageInfo] | dict)
async def get_row_descendants(
    row_id: str,
    max_depth: int = Query(default=10, le=50),
) -> list[RowLineageInfo] | dict[str, str]:
    """Get all descendant rows (recursive)."""
    try:
        rows = await execute_lineage_query(
            """
            WITH RECURSIVE descendants AS (
                SELECT rl.row_id, rl.table_name, rl.source_type,
                       rl.parent_row_ids, rl.created_at, 1 as depth
                FROM phlo.row_lineage rl
                WHERE %s = ANY(rl.parent_row_ids)

                UNION ALL

                SELECT rl.row_id, rl.table_name, rl.source_type,
                       rl.parent_row_ids, rl.created_at, d.depth + 1
                FROM phlo.row_lineage rl
                INNER JOIN descendants d ON d.row_id = ANY(rl.parent_row_ids)
                WHERE d.depth < %s
            )
            SELECT DISTINCT row_id, table_name, source_type,
                   parent_row_ids, created_at
            FROM descendants
            ORDER BY created_at ASC
            """,
            [row_id, max_depth],
        )

        return [row_to_lineage_info(row) for row in rows]
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.exception("Failed to get row descendants")
        return {"error": str(e)}


@router.get("/rows/{row_id}/journey", response_model=LineageJourney | dict)
async def get_row_journey(row_id: str) -> LineageJourney | dict[str, str]:
    """Get full lineage journey for a row (ancestors + self + descendants)."""
    try:
        # Get current row
        current_rows = await execute_lineage_query(
            """
            SELECT row_id, table_name, source_type, parent_row_ids, created_at
            FROM phlo.row_lineage WHERE row_id = %s
            """,
            [row_id],
        )
        current = row_to_lineage_info(current_rows[0]) if current_rows else None

        # Get immediate ancestors
        ancestors_rows = await execute_lineage_query(
            """
            SELECT rl.row_id, rl.table_name, rl.source_type, rl.parent_row_ids, rl.created_at
            FROM phlo.row_lineage rl
            WHERE rl.row_id = ANY(
                SELECT unnest(parent_row_ids)
                FROM phlo.row_lineage
                WHERE row_id = %s
            )
            """,
            [row_id],
        )

        # Get immediate descendants
        descendants_rows = await execute_lineage_query(
            """
            SELECT row_id, table_name, source_type, parent_row_ids, created_at
            FROM phlo.row_lineage
            WHERE %s = ANY(parent_row_ids)
            """,
            [row_id],
        )

        return LineageJourney(
            current=current,
            ancestors=[row_to_lineage_info(row) for row in ancestors_rows],
            descendants=[row_to_lineage_info(row) for row in descendants_rows],
        )
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.exception("Failed to get row journey")
        return {"error": str(e)}


@router.get("/assets", response_model=AssetLineageGraph | dict)
async def get_asset_lineage_graph(
    asset_key: str | None = Query(default=None),
    direction: str = Query(default="both", pattern="^(upstream|downstream|both)$"),
    depth: int | None = Query(default=None, ge=1, le=50),
) -> AssetLineageGraph | dict[str, str]:
    """Get asset-level lineage graph."""
    try:
        nodes = await execute_lineage_query(
            """
            SELECT asset_key, asset_type, status, description, metadata, tags
            FROM phlo.asset_lineage_nodes
            """,
            [],
        )
        edges = await execute_lineage_query(
            """
            SELECT source_asset, target_asset, metadata, tags
            FROM phlo.asset_lineage_edges
            """,
            [],
        )

        assets, edges_map, edge_details = _build_asset_graph(nodes, edges)

        if asset_key:
            if asset_key not in assets:
                return {"error": f"Asset {asset_key} not found in lineage store"}
            assets, edges_map, edge_details = _filter_asset_graph(
                assets,
                edges_map,
                edge_details,
                asset_key=asset_key,
                direction=direction,
                depth=depth,
            )

        return AssetLineageGraph(
            assets=assets,
            edges=edges_map,
            edge_details=edge_details,
        )
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.exception("Failed to get asset lineage graph")
        return {"error": str(e)}
