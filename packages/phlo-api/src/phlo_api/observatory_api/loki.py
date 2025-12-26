"""Loki Log Querying API Router.

Endpoints for querying logs from Loki.
Supports correlation by run_id, asset_key, job_name, and partition_key.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Literal

import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["loki"])

DEFAULT_LOKI_URL = "http://loki:3100"

LogLevel = Literal["debug", "info", "warn", "error"]


def resolve_loki_url(override: str | None = None) -> str:
    """Resolve Loki URL."""
    if override and override.strip():
        return override
    return os.environ.get("LOKI_URL", DEFAULT_LOKI_URL)


# --- Pydantic Models ---


class LogEntry(BaseModel):
    timestamp: str
    level: LogLevel
    message: str
    metadata: dict[str, str]


class LogQueryResult(BaseModel):
    entries: list[LogEntry]
    has_more: bool


class LokiConnectionStatus(BaseModel):
    connected: bool
    error: str | None = None
    version: str | None = None


# --- Helper Functions ---


def build_log_query(
    run_id: str | None = None,
    asset_key: str | None = None,
    job: str | None = None,
    partition_key: str | None = None,
    check_name: str | None = None,
    level: LogLevel | None = None,
    service: str | None = None,
) -> str:
    """Build a LogQL query with optional filters."""
    label_matchers = []
    json_filters = []

    # Service filter - required by Loki
    if service:
        label_matchers.append(f'container=~".*{service}.*"')
    else:
        label_matchers.append('container=~".+"')

    # JSON filters for correlation
    if run_id:
        json_filters.append(f'run_id="{run_id}"')
    if asset_key:
        json_filters.append(f'asset_key="{asset_key}"')
    if job:
        json_filters.append(f'job_name="{job}"')
    if partition_key:
        json_filters.append(f'partition_key="{partition_key}"')
    if check_name:
        json_filters.append(f'check_name="{check_name}"')
    if level:
        json_filters.append(f'level="{level}"')

    label_selector = ", ".join(label_matchers)
    json_pipeline = " | json | " + " | ".join(json_filters) if json_filters else " | json"

    return "{" + label_selector + "}" + json_pipeline


def parse_loki_response(response: dict[str, Any]) -> list[LogEntry]:
    """Parse Loki response into LogEntry list."""
    entries = []

    for stream in response.get("data", {}).get("result", []):
        stream_labels = stream.get("stream", {})
        for timestamp_ns, line in stream.get("values", []):
            try:
                parsed = json.loads(line)
                entries.append(
                    LogEntry(
                        timestamp=datetime.fromtimestamp(
                            int(timestamp_ns) / 1_000_000_000
                        ).isoformat(),
                        level=parsed.get("level", "info"),
                        message=parsed.get("msg") or parsed.get("message") or line,
                        metadata={
                            k: v
                            for k, v in {
                                "run_id": parsed.get("run_id"),
                                "asset_key": parsed.get("asset_key"),
                                "job_name": parsed.get("job_name"),
                                "partition_key": parsed.get("partition_key"),
                                "fn": parsed.get("fn"),
                                "durationMs": str(parsed.get("durationMs"))
                                if parsed.get("durationMs")
                                else None,
                            }.items()
                            if v
                        },
                    )
                )
            except Exception:
                # Non-JSON log line
                entries.append(
                    LogEntry(
                        timestamp=datetime.fromtimestamp(
                            int(timestamp_ns) / 1_000_000_000
                        ).isoformat(),
                        level="info",
                        message=line,
                        metadata=stream_labels,
                    )
                )

    # Sort by timestamp descending
    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return entries


# --- API Endpoints ---


@router.get("/connection", response_model=LokiConnectionStatus)
async def check_connection(loki_url: str | None = None) -> LokiConnectionStatus:
    """Check if Loki is reachable."""
    url = resolve_loki_url(loki_url)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/ready")

            if response.status_code != 200:
                return LokiConnectionStatus(
                    connected=False,
                    error=f"HTTP {response.status_code}: {response.reason_phrase}",
                )

            # Get version
            try:
                build_response = await client.get(f"{url}/loki/api/v1/status/buildinfo")
                version = (
                    build_response.json().get("version", "unknown")
                    if build_response.status_code == 200
                    else "unknown"
                )
            except Exception:
                version = "unknown"

            return LokiConnectionStatus(connected=True, version=version)
    except Exception as e:
        return LokiConnectionStatus(connected=False, error=str(e))


@router.get("/query", response_model=LogQueryResult | dict)
async def query_logs(
    start: str,
    end: str,
    run_id: str | None = None,
    asset_key: str | None = None,
    job: str | None = None,
    partition_key: str | None = None,
    check_name: str | None = None,
    level: LogLevel | None = None,
    service: str | None = None,
    limit: int = Query(default=100, le=1000),
    loki_url: str | None = None,
) -> LogQueryResult | dict[str, str]:
    """Query logs with filters."""
    url = resolve_loki_url(loki_url)

    try:
        query = build_log_query(run_id, asset_key, job, partition_key, check_name, level, service)

        # Convert ISO timestamps to nanoseconds
        start_ns = int(
            datetime.fromisoformat(start.replace("Z", "+00:00")).timestamp() * 1_000_000_000
        )
        end_ns = int(datetime.fromisoformat(end.replace("Z", "+00:00")).timestamp() * 1_000_000_000)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{url}/loki/api/v1/query_range",
                params={
                    "query": query,
                    "start": str(start_ns),
                    "end": str(end_ns),
                    "limit": str(limit),
                    "direction": "backward",
                },
            )
            response.raise_for_status()
            result = response.json()

            entries = parse_loki_response(result)
            return LogQueryResult(entries=entries, has_more=len(entries) == limit)
    except Exception as e:
        logger.exception("Failed to query logs")
        return {"error": str(e)}


@router.get("/runs/{run_id}", response_model=LogQueryResult | dict)
async def query_run_logs(
    run_id: str,
    level: LogLevel | None = None,
    limit: int = Query(default=500, le=2000),
    loki_url: str | None = None,
) -> LogQueryResult | dict[str, str]:
    """Query logs for a specific Dagster run."""
    # Query last 24 hours
    end = datetime.now()
    start = end - timedelta(hours=24)

    return await query_logs(
        start=start.isoformat(),
        end=end.isoformat(),
        run_id=run_id,
        level=level,
        limit=limit,
        loki_url=loki_url,
    )


@router.get("/assets/{asset_key:path}", response_model=LogQueryResult | dict)
async def query_asset_logs(
    asset_key: str,
    partition_key: str | None = None,
    level: LogLevel | None = None,
    hours_back: int = Query(default=24, le=168),
    limit: int = Query(default=200, le=1000),
    loki_url: str | None = None,
) -> LogQueryResult | dict[str, str]:
    """Query logs for a specific asset."""
    end = datetime.now()
    start = end - timedelta(hours=hours_back)

    return await query_logs(
        start=start.isoformat(),
        end=end.isoformat(),
        asset_key=asset_key,
        partition_key=partition_key,
        level=level,
        limit=limit,
        loki_url=loki_url,
    )


@router.get("/labels", response_model=dict)
async def get_log_labels(loki_url: str | None = None) -> dict[str, Any]:
    """Get available log labels for filtering."""
    url = resolve_loki_url(loki_url)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/loki/api/v1/labels")
            response.raise_for_status()
            result = response.json()
            return {"labels": result.get("data", [])}
    except Exception as e:
        return {"error": str(e)}
