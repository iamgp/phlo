"""Quality API Router.

Endpoints for aggregating quality check results from Dagster.
Powers the Quality Center dashboard and asset quality tabs.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Literal

import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["quality"])

DEFAULT_DAGSTER_URL = "http://dagster:3000/graphql"


def resolve_dagster_url(override: str | None = None) -> str:
    """Resolve Dagster GraphQL URL."""
    if override and override.strip():
        return override
    return os.environ.get("DAGSTER_GRAPHQL_URL", DEFAULT_DAGSTER_URL)


# --- GraphQL Query ---

ASSET_CHECK_EXECUTIONS_QUERY = """
query AssetCheckExecutionsQuery($assetKey: AssetKeyInput!, $limit: Int!) {
    assetCheckExecutions(assetKey: $assetKey, limit: $limit) {
        status
        runId
        timestamp
        checkName
        evaluation {
            severity
            metadataEntries {
                __typename
                label
                ... on TextMetadataEntry { text }
                ... on IntMetadataEntry { intValue }
                ... on FloatMetadataEntry { floatValue }
                ... on BoolMetadataEntry { boolValue }
                ... on JsonMetadataEntry { jsonString }
            }
        }
    }
}
"""


# --- Pydantic Models ---

CheckStatus = Literal["PASSED", "FAILED", "IN_PROGRESS", "SKIPPED"]
Severity = Literal["WARN", "ERROR"]


class CheckResult(BaseModel):
    passed: bool
    metadata: dict[str, Any] = {}


class QualityCheck(BaseModel):
    name: str
    asset_key: list[str]
    description: str | None = None
    severity: Severity
    status: CheckStatus
    last_execution_time: str | None = None
    last_result: CheckResult | None = None


class CategoryStats(BaseModel):
    category: str
    passing: int
    total: int
    percentage: int


class QualityOverview(BaseModel):
    total_checks: int
    passing_checks: int
    failing_checks: int
    warning_checks: int
    quality_score: int
    by_category: list[CategoryStats]
    trend: list[dict[str, Any]] = []


class CheckExecution(BaseModel):
    timestamp: str
    passed: bool
    run_id: str | None = None
    metadata: dict[str, Any] = {}


# --- Helper Functions ---


def normalize_status(status: str) -> CheckStatus:
    """Normalize Dagster status to our status enum."""
    normalized = status.strip().upper()
    if normalized == "SUCCEEDED":
        return "PASSED"
    if normalized == "FAILED":
        return "FAILED"
    if normalized == "IN_PROGRESS":
        return "IN_PROGRESS"
    return "SKIPPED"


def normalize_severity(severity: str | None) -> Severity:
    """Normalize severity."""
    return "WARN" if severity == "WARN" else "ERROR"


def to_epoch_ms(value: str | int | float) -> int:
    """Convert timestamp to epoch milliseconds."""
    if isinstance(value, (int, float)):
        if value > 1_000_000_000_000:
            return int(value)
        return int(value * 1000)
    try:
        num = float(value.strip())
        if num > 1_000_000_000_000:
            return int(num)
        return int(num * 1000)
    except ValueError:
        from datetime import datetime

        try:
            return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)
        except Exception:
            return 0


def to_iso_timestamp(value: str | int | float) -> str:
    """Convert to ISO timestamp."""
    from datetime import datetime

    return datetime.fromtimestamp(to_epoch_ms(value) / 1000).isoformat()


def metadata_entries_to_dict(entries: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Convert Dagster metadata entries to a dict."""
    record: dict[str, Any] = {}
    if not entries:
        return record

    for entry in entries:
        label = entry.get("label")
        if not label:
            continue
        typename = entry.get("__typename", "")
        if typename == "TextMetadataEntry":
            record[label] = entry.get("text")
        elif typename == "IntMetadataEntry":
            record[label] = entry.get("intValue")
        elif typename == "FloatMetadataEntry":
            record[label] = entry.get("floatValue")
        elif typename == "BoolMetadataEntry":
            record[label] = entry.get("boolValue")
        elif typename == "JsonMetadataEntry":
            import json

            try:
                record[label] = json.loads(entry.get("jsonString", "{}"))
            except Exception:
                record[label] = entry.get("jsonString")
    return record


# --- API Endpoints ---


@router.get("/overview", response_model=QualityOverview | dict)
async def get_quality_overview(
    dagster_url: str | None = None,
) -> QualityOverview | dict[str, str]:
    """Get overview of all quality metrics."""
    # For now, return a basic structure - full implementation would call Dagster
    # This is a simplified version that can be enhanced later
    url = resolve_dagster_url(dagster_url)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get all checks from Dagster
            # This would need the full quality.dagster.ts logic
            # For now return a placeholder
            return QualityOverview(
                total_checks=0,
                passing_checks=0,
                failing_checks=0,
                warning_checks=0,
                quality_score=100,
                by_category=[],
                trend=[],
            )
    except Exception as e:
        return {"error": str(e)}


@router.get("/assets/{asset_key_path:path}/checks", response_model=list[QualityCheck] | dict)
async def get_asset_checks(
    asset_key_path: str,
    dagster_url: str | None = None,
) -> list[QualityCheck] | dict[str, str]:
    """Get quality checks for a specific asset."""
    asset_key = asset_key_path.split("/")
    url = resolve_dagster_url(dagster_url)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json={
                    "query": ASSET_CHECK_EXECUTIONS_QUERY,
                    "variables": {"assetKey": {"path": asset_key}, "limit": 200},
                },
            )
            response.raise_for_status()
            result = response.json()

            if result.get("errors"):
                return {"error": result["errors"][0].get("message", "GraphQL error")}

            executions = result.get("data", {}).get("assetCheckExecutions", [])

            # Group by check name and get newest
            newest_by_check: dict[str, dict[str, Any]] = {}
            for exec in executions:
                check_name = exec.get("checkName")
                if not check_name:
                    continue
                existing = newest_by_check.get(check_name)
                if not existing or to_epoch_ms(exec["timestamp"]) > to_epoch_ms(
                    existing["timestamp"]
                ):
                    newest_by_check[check_name] = exec

            checks = []
            for check_name, exec in sorted(newest_by_check.items()):
                status = normalize_status(exec.get("status", ""))
                evaluation = exec.get("evaluation") or {}
                checks.append(
                    QualityCheck(
                        name=check_name,
                        asset_key=asset_key,
                        severity=normalize_severity(evaluation.get("severity")),
                        status=status,
                        last_execution_time=to_iso_timestamp(exec["timestamp"]),
                        last_result=CheckResult(
                            passed=status == "PASSED",
                            metadata=metadata_entries_to_dict(evaluation.get("metadataEntries")),
                        ),
                    )
                )
            return checks
    except Exception as e:
        logger.exception("Failed to get asset checks")
        return {"error": str(e)}


@router.get(
    "/assets/{asset_key_path:path}/checks/{check_name}/history",
    response_model=list[CheckExecution] | dict,
)
async def get_check_history(
    asset_key_path: str,
    check_name: str,
    limit: int = Query(default=20, le=100),
    dagster_url: str | None = None,
) -> list[CheckExecution] | dict[str, str]:
    """Get execution history for a specific check."""
    asset_key = asset_key_path.split("/")
    url = resolve_dagster_url(dagster_url)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json={
                    "query": ASSET_CHECK_EXECUTIONS_QUERY,
                    "variables": {"assetKey": {"path": asset_key}, "limit": max(50, limit * 3)},
                },
            )
            response.raise_for_status()
            result = response.json()

            if result.get("errors"):
                return {"error": result["errors"][0].get("message", "GraphQL error")}

            all_executions = result.get("data", {}).get("assetCheckExecutions", [])

            # Filter by check name
            executions = [e for e in all_executions if e.get("checkName") == check_name]

            # Sort by timestamp descending
            executions.sort(key=lambda e: to_epoch_ms(e["timestamp"]), reverse=True)

            return [
                CheckExecution(
                    timestamp=to_iso_timestamp(e["timestamp"]),
                    passed=normalize_status(e.get("status", "")) == "PASSED",
                    run_id=e.get("runId"),
                    metadata=metadata_entries_to_dict(
                        (e.get("evaluation") or {}).get("metadataEntries")
                    ),
                )
                for e in executions[:limit]
            ]
    except Exception as e:
        logger.exception("Failed to get check history")
        return {"error": str(e)}


@router.get("/failing", response_model=list[QualityCheck] | dict)
async def get_failing_checks(
    dagster_url: str | None = None,
) -> list[QualityCheck] | dict[str, str]:
    """Get all currently failing checks."""
    # This would need to iterate over all assets
    # For now return empty - can be enhanced later
    return []
