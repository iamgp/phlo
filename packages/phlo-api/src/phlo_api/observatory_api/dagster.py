"""Dagster API Router.

Endpoints for interacting with the Dagster GraphQL API.
Provides health metrics, asset listing, and materialization history.
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel

from phlo.logging import get_logger
from phlo_api.observatory_api.quality import fetch_quality_snapshot

logger = get_logger(__name__)

router = APIRouter(tags=["dagster"])

DEFAULT_DAGSTER_URL = "http://dagster:3000/graphql"


def resolve_dagster_url(override: str | None = None) -> str:
    """Resolve the Dagster GraphQL URL from override, environment, or default."""
    env_url = os.environ.get("DAGSTER_GRAPHQL_URL")
    if override and override.strip():
        if env_url and override.strip() == "http://localhost:3000/graphql":
            return env_url
        return override
    return env_url or DEFAULT_DAGSTER_URL


# --- GraphQL Queries ---

VERSION_QUERY = """
query Version {
    version
}
"""

HEALTH_QUERY = """
query HealthMetrics {
    assetsOrError {
        ... on AssetConnection {
            nodes {
                key { path }
                assetMaterializations(limit: 1) {
                    timestamp
                }
            }
        }
        ... on PythonError { message }
    }
    runsOrError(filter: { statuses: [FAILURE] }, limit: 100) {
        ... on Runs {
            results {
                id
                status
                startTime
                endTime
            }
        }
        ... on PythonError { message }
    }
}
"""

ASSETS_QUERY = """
query AssetsQuery {
    assetsOrError {
        __typename
        ... on AssetConnection {
            nodes {
                id
                key { path }
                definition {
                    description
                    computeKind
                    groupName
                    hasMaterializePermission
                    opNames
                }
                assetMaterializations(limit: 1) {
                    timestamp
                    runId
                }
            }
        }
        ... on PythonError { message }
    }
}
"""

ASSET_GRAPH_QUERY = """
query AssetGraphQuery {
    assetsOrError {
        __typename
        ... on AssetConnection {
            nodes {
                id
                key { path }
                definition {
                    description
                    computeKind
                    groupName
                    dependencyKeys { path }
                    dependedByKeys { path }
                }
                assetMaterializations(limit: 1) {
                    timestamp
                }
            }
        }
        ... on PythonError { message }
    }
}
"""

ASSET_DETAILS_QUERY = """
query AssetDetailsQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
        ... on Asset {
            id
            key { path }
            definition {
                description
                computeKind
                groupName
                hasMaterializePermission
                opNames
                metadataEntries {
                    label
                    description
                    ... on TextMetadataEntry { text }
                    ... on TableSchemaMetadataEntry {
                        schema {
                            columns { name type description }
                        }
                    }
                    ... on TableColumnLineageMetadataEntry {
                        lineage {
                            columnName
                            columnDeps {
                                assetKey { path }
                                columnName
                            }
                        }
                    }
                }
                partitionDefinition { description }
            }
            assetMaterializations(limit: 1) {
                timestamp
                runId
                metadataEntries {
                    label
                    __typename
                    ... on TableSchemaMetadataEntry {
                        schema {
                            columns { name type description }
                        }
                    }
                    ... on TableColumnLineageMetadataEntry {
                        lineage {
                            columnName
                            columnDeps {
                                assetKey { path }
                                columnName
                            }
                        }
                    }
                }
            }
        }
        ... on AssetNotFoundError { message }
    }
}
"""

MATERIALIZATION_HISTORY_QUERY = """
query MaterializationHistory($assetKey: AssetKeyInput!, $limit: Int!) {
    assetOrError(assetKey: $assetKey) {
        ... on Asset {
            assetMaterializations(limit: $limit) {
                timestamp
                runId
                stepKey
                metadataEntries {
                    label
                    ... on TextMetadataEntry { text }
                    ... on IntMetadataEntry { intValue }
                    ... on FloatMetadataEntry { floatValue }
                }
            }
        }
        ... on AssetNotFoundError { message }
    }
}
"""


# --- Pydantic Models ---


class DagsterConnectionStatus(BaseModel):
    """Connection status and server version metadata for Dagster."""

    connected: bool
    error: str | None = None
    version: str | None = None


class HealthMetrics(BaseModel):
    """Aggregated platform health metrics exposed to Observatory."""

    assets_total: int
    assets_healthy: int
    failed_jobs_24h: int
    quality_checks_passing: int
    quality_checks_total: int
    stale_assets: int
    last_updated: str


class LastMaterialization(BaseModel):
    """Timestamp and run id for the most recent materialization."""

    timestamp: str
    run_id: str


class Asset(BaseModel):
    """Dagster asset summary used in list views."""

    id: str
    key: list[str]
    key_path: str
    description: str | None = None
    compute_kind: str | None = None
    group_name: str | None = None
    last_materialization: LastMaterialization | None = None
    has_materialize_permission: bool = False


class ColumnSchema(BaseModel):
    """Column definition extracted from metadata."""

    name: str
    type: str
    description: str | None = None


class ColumnLineageDep(BaseModel):
    """Single upstream column dependency for lineage rendering."""

    asset_key: list[str]
    column_name: str


class AssetDetails(Asset):
    """Extended asset payload used on detail pages."""

    op_names: list[str] = []
    metadata: list[dict[str, str]] = []
    columns: list[ColumnSchema] | None = None
    column_lineage: dict[str, list[ColumnLineageDep]] | None = None
    partition_definition: dict[str, str] | None = None


class MaterializationEvent(BaseModel):
    """Single historical materialization event for an asset."""

    timestamp: str
    run_id: str
    status: str = "SUCCESS"
    step_key: str | None = None
    metadata: list[dict[str, str]] = []
    duration: int | None = None


class GraphNode(BaseModel):
    """Graph node payload used by Observatory graph views."""

    id: str
    key: list[str]
    key_path: str
    label: str
    description: str | None = None
    compute_kind: str | None = None
    group_name: str | None = None
    layer: str
    last_materialization: str | None = None
    upstream_count: int
    downstream_count: int


class GraphEdge(BaseModel):
    """Directed edge between two graph nodes."""

    source: str
    target: str


class AssetGraphPayload(BaseModel):
    """Full asset graph payload for Observatory."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ImpactedAsset(BaseModel):
    """Single downstream impact result for an asset."""

    key_path: str
    label: str
    layer: str
    depth: int


# --- Helper Functions ---


async def graphql_request(
    url: str, query: str, variables: dict[str, Any] | None = None, timeout: float = 10.0
) -> dict[str, Any]:
    """Execute a GraphQL request."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            url,
            json={"query": query, "variables": variables or {}},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()


def infer_layer(key_path: str) -> str:
    """Infer logical data layer from asset key path."""
    path = key_path.lower()
    if "publish" in path or path.startswith("publish_"):
        return "publish"
    if "mart" in path or path.startswith("mrt_"):
        return "marts"
    if "gold" in path or path.startswith("dim_") or path.startswith("fct_"):
        return "gold"
    if "silver" in path or "stg_" in path:
        return "silver"
    if "bronze" in path or "raw" in path:
        return "bronze"
    if path.startswith("dlt_") or "ingest" in path:
        return "bronze"
    if path.startswith("src_") or "source" in path:
        return "source"
    return "unknown"


def build_asset_graph_payload(asset_nodes: list[dict[str, Any]]) -> AssetGraphPayload:
    """Build the normalized Observatory graph payload from Dagster nodes."""
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    known_nodes: set[str] = set()

    for asset in asset_nodes:
        key = asset["key"]["path"]
        key_path = "/".join(key)
        definition = asset.get("definition") or {}
        known_nodes.add(key_path)
        nodes.append(
            GraphNode(
                id=asset["id"],
                key=key,
                key_path=key_path,
                label=key[-1] if key else key_path,
                description=definition.get("description"),
                compute_kind=definition.get("computeKind"),
                group_name=definition.get("groupName"),
                layer=infer_layer(key_path),
                last_materialization=((asset.get("assetMaterializations") or [None])[0] or {}).get(
                    "timestamp"
                ),
                upstream_count=len(definition.get("dependencyKeys") or []),
                downstream_count=len(definition.get("dependedByKeys") or []),
            )
        )

    for asset in asset_nodes:
        target_key_path = "/".join(asset["key"]["path"])
        dependencies = (asset.get("definition") or {}).get("dependencyKeys") or []
        for dependency in dependencies:
            source_key_path = "/".join(dependency["path"])
            if source_key_path in known_nodes and target_key_path in known_nodes:
                edges.append(GraphEdge(source=source_key_path, target=target_key_path))

    return AssetGraphPayload(nodes=nodes, edges=edges)


def filter_asset_neighbors(
    graph: AssetGraphPayload,
    asset_key: str,
    direction: str,
    depth: int,
) -> AssetGraphPayload:
    """Return a focused subgraph around an asset."""
    upstream: dict[str, list[str]] = {}
    downstream: dict[str, list[str]] = {}

    for edge in graph.edges:
        upstream.setdefault(edge.target, []).append(edge.source)
        downstream.setdefault(edge.source, []).append(edge.target)

    included_nodes = {asset_key}

    def bfs(start_key: str, adjacency: dict[str, list[str]], max_depth: int) -> None:
        queue: list[tuple[str, int]] = [(start_key, 0)]
        visited = {start_key}

        while queue:
            current, current_depth = queue.pop(0)
            if current_depth >= max_depth:
                continue

            for neighbor in adjacency.get(current, []):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                included_nodes.add(neighbor)
                queue.append((neighbor, current_depth + 1))

    if direction in {"upstream", "both"}:
        bfs(asset_key, upstream, depth)
    if direction in {"downstream", "both"}:
        bfs(asset_key, downstream, depth)

    return AssetGraphPayload(
        nodes=[node for node in graph.nodes if node.key_path in included_nodes],
        edges=[
            edge
            for edge in graph.edges
            if edge.source in included_nodes and edge.target in included_nodes
        ],
    )


def compute_asset_impact(
    graph: AssetGraphPayload, asset_key: str, max_depth: int
) -> list[ImpactedAsset]:
    """Compute all downstream assets impacted by a given asset."""
    node_map = {node.key_path: node for node in graph.nodes}
    downstream: dict[str, list[str]] = {}
    for edge in graph.edges:
        downstream.setdefault(edge.source, []).append(edge.target)

    impacted: list[ImpactedAsset] = []
    visited = {asset_key}
    queue: list[tuple[str, int]] = [(asset_key, 0)]

    while queue:
        current, current_depth = queue.pop(0)
        if current_depth > max_depth:
            continue

        for child in downstream.get(current, []):
            if child in visited:
                continue
            visited.add(child)
            node = node_map.get(child)
            if node is not None:
                impacted.append(
                    ImpactedAsset(
                        key_path=node.key_path,
                        label=node.label,
                        layer=node.layer,
                        depth=current_depth + 1,
                    )
                )
            queue.append((child, current_depth + 1))

    return sorted(impacted, key=lambda item: (item.depth, item.label))


# --- API Endpoints ---


@router.get("/connection", response_model=DagsterConnectionStatus)
async def check_connection(dagster_url: str | None = None) -> DagsterConnectionStatus:
    """Check if Dagster is reachable."""
    url = resolve_dagster_url(dagster_url)

    try:
        result = await graphql_request(url, VERSION_QUERY, timeout=5.0)

        if result.get("errors"):
            return DagsterConnectionStatus(
                connected=False, error=result["errors"][0].get("message", "GraphQL error")
            )

        return DagsterConnectionStatus(
            connected=True, version=result.get("data", {}).get("version")
        )
    except Exception as e:
        return DagsterConnectionStatus(connected=False, error=str(e))


@router.get("/health", response_model=HealthMetrics | dict)
async def get_health_metrics(
    dagster_url: str | None = None,
) -> HealthMetrics | dict[str, str]:
    """Get health metrics from Dagster."""
    url = resolve_dagster_url(dagster_url)

    try:
        result = await graphql_request(url, HEALTH_QUERY)

        if result.get("errors"):
            return {"error": result["errors"][0].get("message", "GraphQL error")}

        data = result.get("data", {})
        assets_or_error = data.get("assetsOrError", {})
        runs_or_error = data.get("runsOrError", {})

        # Handle asset data
        assets_total = 0
        stale_assets = 0
        now = time.time() * 1000
        stale_threshold = 24 * 60 * 60 * 1000  # 24 hours

        if assets_or_error.get("nodes"):
            nodes = assets_or_error["nodes"]
            assets_total = len(nodes)

            for asset in nodes:
                last_mat = (asset.get("assetMaterializations") or [None])[0]
                if last_mat:
                    mat_time = float(last_mat.get("timestamp", 0)) * 1000
                    if now - mat_time > stale_threshold:
                        stale_assets += 1
                else:
                    stale_assets += 1

        # Handle run data
        failed_jobs_24h = 0
        one_day_ago = now - stale_threshold

        if runs_or_error.get("results"):
            for run in runs_or_error["results"]:
                start_time = float(run.get("startTime") or 0) * 1000
                if start_time > one_day_ago:
                    failed_jobs_24h += 1

        quality_checks_passing = 0
        quality_checks_total = 0
        quality_snapshot = await fetch_quality_snapshot(url)
        if quality_snapshot:
            quality_checks_passing = quality_snapshot["passing_checks"]
            quality_checks_total = quality_snapshot["total_checks"]

        return HealthMetrics(
            assets_total=assets_total,
            assets_healthy=assets_total - stale_assets,
            failed_jobs_24h=failed_jobs_24h,
            quality_checks_passing=quality_checks_passing,
            quality_checks_total=quality_checks_total,
            stale_assets=stale_assets,
            last_updated=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.exception("Failed to get health metrics")
        return {"error": str(e)}


@router.get("/assets", response_model=list[Asset] | dict)
async def get_assets(dagster_url: str | None = None) -> list[Asset] | dict[str, str]:
    """Get all assets from Dagster."""
    url = resolve_dagster_url(dagster_url)

    try:
        result = await graphql_request(url, ASSETS_QUERY)

        if result.get("errors"):
            return {"error": result["errors"][0].get("message", "GraphQL error")}

        data = result.get("data", {})
        assets_or_error = data.get("assetsOrError", {})

        if assets_or_error.get("message"):  # PythonError
            return {"error": assets_or_error["message"]}

        assets = []
        for node in assets_or_error.get("nodes", []):
            definition = node.get("definition") or {}
            mats = node.get("assetMaterializations") or []

            last_mat = None
            if mats:
                last_mat = LastMaterialization(
                    timestamp=mats[0]["timestamp"], run_id=mats[0]["runId"]
                )

            assets.append(
                Asset(
                    id=node["id"],
                    key=node["key"]["path"],
                    key_path="/".join(node["key"]["path"]),
                    description=definition.get("description"),
                    compute_kind=definition.get("computeKind"),
                    group_name=definition.get("groupName"),
                    has_materialize_permission=definition.get("hasMaterializePermission", False),
                    last_materialization=last_mat,
                )
            )

        return assets
    except Exception as e:
        logger.exception("Failed to get assets")
        return {"error": str(e)}


@router.get("/assets/{asset_key_path:path}", response_model=AssetDetails | dict)
async def get_asset_details(
    asset_key_path: str, dagster_url: str | None = None
) -> AssetDetails | dict[str, str]:
    """Get detailed information about a single asset."""
    if not asset_key_path:
        return {"error": "Asset key is required"}

    url = resolve_dagster_url(dagster_url)
    asset_key = asset_key_path.split("/")

    try:
        result = await graphql_request(url, ASSET_DETAILS_QUERY, {"assetKey": {"path": asset_key}})

        if result.get("errors"):
            return {"error": result["errors"][0].get("message", "GraphQL error")}

        asset_or_error = result.get("data", {}).get("assetOrError", {})

        if asset_or_error.get("message"):  # AssetNotFoundError
            return {"error": asset_or_error["message"]}

        definition = asset_or_error.get("definition") or {}
        mats = asset_or_error.get("assetMaterializations") or []

        # Extract columns from metadata
        columns = None
        column_lineage = None

        # Check materialization metadata first, then definition
        for source in [mats[0] if mats else None, definition]:
            if not source:
                continue
            for entry in source.get("metadataEntries", []):
                if entry.get("schema") and not columns:
                    columns = [
                        ColumnSchema(
                            name=c["name"],
                            type=c["type"],
                            description=c.get("description"),
                        )
                        for c in entry["schema"].get("columns", [])
                    ]
                if entry.get("lineage") and not column_lineage:
                    column_lineage = {}
                    for lin in entry["lineage"]:
                        column_lineage[lin["columnName"]] = [
                            ColumnLineageDep(
                                asset_key=dep["assetKey"]["path"],
                                column_name=dep["columnName"],
                            )
                            for dep in lin.get("columnDeps", [])
                        ]

        last_mat = None
        if mats:
            last_mat = LastMaterialization(timestamp=mats[0]["timestamp"], run_id=mats[0]["runId"])

        return AssetDetails(
            id=asset_or_error["id"],
            key=asset_or_error["key"]["path"],
            key_path="/".join(asset_or_error["key"]["path"]),
            description=definition.get("description"),
            compute_kind=definition.get("computeKind"),
            group_name=definition.get("groupName"),
            has_materialize_permission=definition.get("hasMaterializePermission", False),
            op_names=definition.get("opNames", []),
            metadata=[
                {"key": e["label"], "value": e.get("text") or e.get("description") or ""}
                for e in definition.get("metadataEntries", [])
                if not e.get("schema")
            ],
            columns=columns,
            column_lineage=column_lineage,
            partition_definition=(
                {"description": definition["partitionDefinition"]["description"]}
                if definition.get("partitionDefinition")
                else None
            ),
            last_materialization=last_mat,
        )
    except Exception as e:
        logger.exception("Failed to get asset details")
        return {"error": str(e)}


@router.get(
    "/assets/{asset_key_path:path}/history", response_model=list[MaterializationEvent] | dict
)
async def get_materialization_history(
    asset_key_path: str,
    limit: int = Query(default=20, le=100),
    dagster_url: str | None = None,
) -> list[MaterializationEvent] | dict[str, str]:
    """Get materialization history for an asset."""
    url = resolve_dagster_url(dagster_url)
    asset_key = asset_key_path.split("/")

    try:
        result = await graphql_request(
            url,
            MATERIALIZATION_HISTORY_QUERY,
            {"assetKey": {"path": asset_key}, "limit": limit},
        )

        if result.get("errors"):
            return {"error": result["errors"][0].get("message", "GraphQL error")}

        asset_or_error = result.get("data", {}).get("assetOrError", {})

        if asset_or_error.get("message"):
            return {"error": asset_or_error["message"]}

        events = []
        for mat in asset_or_error.get("assetMaterializations", []):
            events.append(
                MaterializationEvent(
                    timestamp=mat["timestamp"],
                    run_id=mat["runId"],
                    status="SUCCESS",
                    step_key=mat.get("stepKey"),
                    metadata=[
                        {
                            "key": e["label"],
                            "value": e.get("text")
                            or str(e.get("intValue", ""))
                            or str(e.get("floatValue", ""))
                            or "",
                        }
                        for e in mat.get("metadataEntries", [])
                    ],
                )
            )

        return events
    except Exception as e:
        logger.exception("Failed to get materialization history")
        return {"error": str(e)}


@router.get("/graph", response_model=AssetGraphPayload | dict)
async def get_asset_graph(
    dagster_url: str | None = None,
) -> AssetGraphPayload | dict[str, str]:
    """Get the full asset dependency graph from Dagster."""
    url = resolve_dagster_url(dagster_url)

    try:
        result = await graphql_request(url, ASSET_GRAPH_QUERY, timeout=15.0)
        if result.get("errors"):
            return {"error": result["errors"][0].get("message", "GraphQL error")}

        assets_or_error = result.get("data", {}).get("assetsOrError", {})
        if assets_or_error.get("__typename") == "PythonError" or assets_or_error.get("message"):
            return {"error": assets_or_error.get("message", "Dagster error")}

        return build_asset_graph_payload(assets_or_error.get("nodes", []))
    except Exception as e:
        logger.exception("Failed to get asset graph")
        return {"error": str(e)}


@router.get("/graph/neighbors", response_model=AssetGraphPayload | dict)
async def get_asset_neighbors(
    asset_key: str,
    direction: str = Query(default="both", pattern="^(upstream|downstream|both)$"),
    depth: int = Query(default=2, ge=1, le=10),
    dagster_url: str | None = None,
) -> AssetGraphPayload | dict[str, str]:
    """Get a focused graph around a single asset."""
    graph = await get_asset_graph(dagster_url=dagster_url)
    if isinstance(graph, dict):
        return graph
    return filter_asset_neighbors(graph, asset_key=asset_key, direction=direction, depth=depth)


@router.get("/graph/impact", response_model=list[ImpactedAsset] | dict)
async def get_asset_impact(
    asset_key: str,
    max_depth: int = Query(default=99, ge=1, le=100),
    dagster_url: str | None = None,
) -> list[ImpactedAsset] | dict[str, str]:
    """Get downstream impact analysis for a single asset."""
    graph = await get_asset_graph(dagster_url=dagster_url)
    if isinstance(graph, dict):
        return graph
    return compute_asset_impact(graph, asset_key=asset_key, max_depth=max_depth)
