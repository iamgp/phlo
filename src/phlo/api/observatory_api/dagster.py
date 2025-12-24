"""Dagster API Router.

Endpoints for interacting with the Dagster GraphQL API.
Provides health metrics, asset listing, and materialization history.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

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
    connected: bool
    error: str | None = None
    version: str | None = None


class HealthMetrics(BaseModel):
    assets_total: int
    assets_healthy: int
    failed_jobs_24h: int
    quality_checks_passing: int
    quality_checks_total: int
    stale_assets: int
    last_updated: str


class LastMaterialization(BaseModel):
    timestamp: str
    run_id: str


class Asset(BaseModel):
    id: str
    key: list[str]
    key_path: str
    description: str | None = None
    compute_kind: str | None = None
    group_name: str | None = None
    last_materialization: LastMaterialization | None = None
    has_materialize_permission: bool = False


class ColumnSchema(BaseModel):
    name: str
    type: str
    description: str | None = None


class ColumnLineageDep(BaseModel):
    asset_key: list[str]
    column_name: str


class AssetDetails(Asset):
    op_names: list[str] = []
    metadata: list[dict[str, str]] = []
    columns: list[ColumnSchema] | None = None
    column_lineage: dict[str, list[ColumnLineageDep]] | None = None
    partition_definition: dict[str, str] | None = None


class MaterializationEvent(BaseModel):
    timestamp: str
    run_id: str
    status: str = "SUCCESS"
    step_key: str | None = None
    metadata: list[dict[str, str]] = []
    duration: int | None = None


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

        return HealthMetrics(
            assets_total=assets_total,
            assets_healthy=assets_total - stale_assets,
            failed_jobs_24h=failed_jobs_24h,
            quality_checks_passing=0,  # TODO: Integrate quality checks
            quality_checks_total=0,
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
