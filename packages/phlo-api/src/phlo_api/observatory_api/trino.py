"""Trino API Router.

Endpoints for executing queries against Trino via HTTP API.
Enables data preview, column profiling, and table metrics in Observatory.
"""

from __future__ import annotations

import asyncio
import os
from time import monotonic
from typing import Any

import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from phlo.logging import get_logger
from phlo_api.observatory_api.trino_sql import (
    is_probably_qualified_table,
    qualify_table_name,
    quote_identifier,
    sql_literal,
    validate_read_only_query,
)

logger = get_logger(__name__)

router = APIRouter(tags=["trino"])

DEFAULT_CATALOG = "iceberg"
DEFAULT_TRINO_URL = "http://trino:8080"


def resolve_trino_url(override: str | None = None) -> str:
    """Resolve the Trino URL from override, environment, or default."""
    env_url = os.environ.get("TRINO_URL")
    if override and override.strip():
        if env_url and override.strip() == "http://localhost:8080":
            return env_url
        return override
    return env_url or DEFAULT_TRINO_URL


# --- Pydantic Models ---


class TrinoConnectionStatus(BaseModel):
    """Connection health and version details for the Trino endpoint."""

    connected: bool
    error: str | None = None
    cluster_version: str | None = None


class DataRow(BaseModel):
    """A row of data with dynamic columns."""

    model_config = {"extra": "allow"}


class DataPreviewResult(BaseModel):
    """Paginated table preview payload returned to the UI."""

    columns: list[str]
    column_types: list[str]
    rows: list[dict[str, Any]]
    total_rows: int | None = None
    has_more: bool


class ColumnProfile(BaseModel):
    """Per-column profiling metrics for a sampled table."""

    column: str
    type: str
    null_count: int
    null_percentage: float
    distinct_count: int
    min_value: str | None = None
    max_value: str | None = None
    sample_values: list[str] | None = None


class TableMetrics(BaseModel):
    """High-level row and storage metrics for a table."""

    row_count: int
    size_bytes: int | None = None
    last_modified: str | None = None
    partition_count: int | None = None


class QueryExecutionResult(BaseModel):
    """Normalized successful query response shape."""

    columns: list[str]
    column_types: list[str]
    rows: list[dict[str, Any]]
    has_more: bool
    effective_query: str | None = None


class QueryExecutionError(BaseModel):
    """Structured query execution failure payload."""

    ok: bool = False
    error: str
    kind: str  # 'timeout', 'trino', 'validation'


# --- Core Query Execution ---


async def execute_trino_query(
    query: str,
    catalog: str = DEFAULT_CATALOG,
    schema: str = "main",
    trino_url: str | None = None,
    timeout_ms: int = 30000,
) -> dict[str, Any] | QueryExecutionError:
    """Execute a query against Trino and wait for results.

    Trino uses a multi-stage query execution model with polling.
    """
    url = resolve_trino_url(trino_url)
    timeout = timeout_ms / 1000.0

    try:
        start_time = monotonic()
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Submit query
            response = await client.post(
                f"{url}/v1/statement",
                content=query,
                headers={
                    "Content-Type": "text/plain",
                    "X-Trino-User": "observatory",
                    "X-Trino-Catalog": catalog,
                    "X-Trino-Schema": schema,
                },
            )

            if response.status_code != 200:
                return QueryExecutionError(error=f"Trino error: {response.text}", kind="trino")

            result = response.json()

            # Poll until query completes
            max_polls = 100
            polls = 0
            all_data: list[list[Any]] = []
            columns: list[str] = []
            column_types: list[str] = []

            while result.get("nextUri") and polls < max_polls:
                polls += 1
                elapsed = monotonic() - start_time
                remaining = timeout - elapsed
                if remaining <= 0:
                    return QueryExecutionError(error="Query timed out", kind="timeout")
                await asyncio.sleep(0.1)

                poll_response = await client.get(
                    result["nextUri"],
                    headers={"X-Trino-User": "observatory"},
                    timeout=remaining,
                )

                if poll_response.status_code != 200:
                    return QueryExecutionError(
                        error=f"Trino poll error: {poll_response.text}", kind="trino"
                    )

                result = poll_response.json()

                if result.get("columns") and not columns:
                    columns = [c["name"] for c in result["columns"]]
                    column_types = [c["type"] for c in result["columns"]]

                if result.get("data"):
                    all_data.extend(result["data"])

                if result.get("error"):
                    return QueryExecutionError(
                        error=result["error"].get("message", "Query failed"),
                        kind="trino",
                    )

            # Convert to row dicts
            rows = [{col: row[idx] for idx, col in enumerate(columns)} for row in all_data]

            return {"columns": columns, "column_types": column_types, "rows": rows}

    except httpx.TimeoutException:
        return QueryExecutionError(error="Query timed out", kind="timeout")
    except Exception as e:
        logger.exception("Trino query failed")
        return QueryExecutionError(error=str(e), kind="trino")


# --- API Endpoints ---


@router.get("/connection", response_model=TrinoConnectionStatus)
async def check_connection(trino_url: str | None = None) -> TrinoConnectionStatus:
    """Check if Trino is reachable."""
    url = resolve_trino_url(trino_url)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/v1/info")

            if response.status_code != 200:
                return TrinoConnectionStatus(
                    connected=False,
                    error=f"HTTP {response.status_code}: {response.reason_phrase}",
                )

            info = response.json()
            return TrinoConnectionStatus(
                connected=True,
                cluster_version=info.get("nodeVersion", {}).get("version", "unknown"),
            )
    except Exception as e:
        return TrinoConnectionStatus(connected=False, error=str(e))


@router.get("/preview/{table:path}", response_model=DataPreviewResult | dict)
async def preview_data(
    table: str,
    branch: str = "main",
    catalog: str | None = None,
    schema: str | None = None,
    limit: int = Query(default=100, le=5000),
    offset: int = Query(default=0, ge=0),
    trino_url: str | None = None,
    timeout_ms: int = Query(default=30000, le=120000),
) -> DataPreviewResult | dict[str, str]:
    """Preview data from a table with pagination."""
    effective_catalog = catalog or DEFAULT_CATALOG
    effective_schema = schema or branch

    resolved_table = (
        table
        if is_probably_qualified_table(table)
        else qualify_table_name(effective_catalog, effective_schema, table)
    )

    # Build query
    if offset > 0:
        query = f"SELECT * FROM {resolved_table} OFFSET {offset} ROWS FETCH FIRST {limit} ROWS ONLY"
    else:
        query = f"SELECT * FROM {resolved_table} LIMIT {limit}"

    result = await execute_trino_query(
        query, effective_catalog, effective_schema, trino_url, timeout_ms
    )

    if isinstance(result, QueryExecutionError):
        return {"error": result.error}

    return DataPreviewResult(
        columns=result["columns"],
        column_types=result["column_types"],
        rows=result["rows"],
        has_more=len(result["rows"]) == limit,
    )


@router.get("/profile/{table:path}/{column}", response_model=ColumnProfile | dict)
async def profile_column(
    table: str,
    column: str,
    branch: str = "main",
    catalog: str | None = None,
    schema: str | None = None,
    trino_url: str | None = None,
    timeout_ms: int = Query(default=30000, le=120000),
) -> ColumnProfile | dict[str, str]:
    """Get column statistics/profile."""
    effective_catalog = catalog or DEFAULT_CATALOG
    effective_schema = schema or branch

    resolved_table = (
        table
        if is_probably_qualified_table(table)
        else qualify_table_name(effective_catalog, effective_schema, table)
    )

    query = f"""
        SELECT
            COUNT(*) as total_count,
            COUNT("{column}") as non_null_count,
            COUNT(DISTINCT "{column}") as distinct_count,
            MIN(CAST("{column}" AS VARCHAR)) as min_value,
            MAX(CAST("{column}" AS VARCHAR)) as max_value
        FROM {resolved_table}
    """

    result = await execute_trino_query(
        query, effective_catalog, effective_schema, trino_url, timeout_ms
    )

    if isinstance(result, QueryExecutionError):
        return {"error": result.error}

    if not result["rows"]:
        return {"error": "No data returned from profile query"}

    row = result["rows"][0]
    total_count = int(row.get("total_count") or 0)
    non_null_count = int(row.get("non_null_count") or 0)
    null_count = total_count - non_null_count

    return ColumnProfile(
        column=column,
        type="unknown",
        null_count=null_count,
        null_percentage=(null_count / total_count * 100) if total_count > 0 else 0,
        distinct_count=int(row.get("distinct_count") or 0),
        min_value=row.get("min_value"),
        max_value=row.get("max_value"),
    )


@router.get("/metrics/{table:path}", response_model=TableMetrics | dict)
async def get_table_metrics(
    table: str,
    branch: str = "main",
    catalog: str | None = None,
    schema: str | None = None,
    trino_url: str | None = None,
    timeout_ms: int = Query(default=30000, le=120000),
) -> TableMetrics | dict[str, str]:
    """Get table-level metrics (row count, etc)."""
    effective_catalog = catalog or DEFAULT_CATALOG
    effective_schema = schema or branch

    resolved_table = (
        table
        if is_probably_qualified_table(table)
        else qualify_table_name(effective_catalog, effective_schema, table)
    )

    query = f"SELECT COUNT(*) as row_count FROM {resolved_table}"

    result = await execute_trino_query(
        query, effective_catalog, effective_schema, trino_url, timeout_ms
    )

    if isinstance(result, QueryExecutionError):
        return {"error": result.error}

    if not result["rows"]:
        return {"error": "No data returned from count query"}

    return TableMetrics(row_count=int(result["rows"][0].get("row_count") or 0))


@router.post("/query", response_model=QueryExecutionResult | QueryExecutionError)
async def execute_query(request: ExecuteQueryRequest) -> QueryExecutionResult | QueryExecutionError:
    """Run an arbitrary query (with guardrails)."""
    effective_catalog = request.catalog or DEFAULT_CATALOG
    effective_schema = request.schema_name or request.branch

    if request.read_only_mode:
        validation_error = validate_read_only_query(request.query)
        if validation_error:
            return QueryExecutionError(error=validation_error, kind="validation")

    result = await execute_trino_query(
        request.query,
        effective_catalog,
        effective_schema,
        request.trino_url,
        request.timeout_ms,
    )

    if isinstance(result, QueryExecutionError):
        return result

    return QueryExecutionResult(
        columns=result["columns"],
        column_types=result["column_types"],
        rows=result["rows"],
        has_more=False,
        effective_query=request.query,
    )


class ExecuteQueryRequest(BaseModel):
    """Payload for executing an ad-hoc Trino query."""

    query: str
    branch: str = "main"
    catalog: str | None = None
    schema_name: str | None = Field(default=None, alias="schema")
    trino_url: str | None = None
    timeout_ms: int = 30000
    read_only_mode: bool = True
    default_limit: int = 100
    max_limit: int = 5000


class QueryWithFiltersRequest(BaseModel):
    """Payload for filtered table preview queries."""

    table_name: str
    schema_name: str = Field(alias="schema")
    catalog: str = DEFAULT_CATALOG
    filters: dict[str, Any]
    limit: int = 10
    trino_url: str | None = None
    timeout_ms: int = 30000


@router.post("/query-with-filters", response_model=DataPreviewResult | dict)
async def query_with_filters(
    request: QueryWithFiltersRequest,
) -> DataPreviewResult | dict[str, str]:
    """Query a table with a simple equality filter map."""
    try:
        catalog = request.catalog or DEFAULT_CATALOG
        table = request.table_name
        schema = request.schema_name

        if not request.filters:
            return DataPreviewResult(columns=[], column_types=[], rows=[], has_more=False)

        resolved_table = qualify_table_name(catalog, schema, table)

        where_parts: list[str] = []
        for column, value in request.filters.items():
            quoted_column = quote_identifier(column)
            if value is None:
                where_parts.append(f"{quoted_column} IS NULL")
            else:
                where_parts.append(f"{quoted_column} = {sql_literal(value)}")

        where_clause = " AND ".join(where_parts)
        limit = int(request.limit)
        if limit <= 0 or limit > 5000:
            raise ValueError("limit must be between 1 and 5000")

        query = f"SELECT * FROM {resolved_table} WHERE {where_clause} LIMIT {limit}"
        result = await execute_trino_query(
            query,
            catalog=catalog,
            schema=schema,
            trino_url=request.trino_url,
            timeout_ms=request.timeout_ms,
        )

        if isinstance(result, QueryExecutionError):
            return {"error": result.error}

        return DataPreviewResult(
            columns=result["columns"],
            column_types=result["column_types"],
            rows=result["rows"],
            has_more=False,
        )
    except ValueError as e:
        return {"error": str(e)}


@router.get("/row/{table:path}/{row_id}", response_model=DataPreviewResult | dict)
async def get_row_by_id(
    table: str,
    row_id: str,
    catalog: str | None = None,
    schema: str | None = None,
    trino_url: str | None = None,
    timeout_ms: int = Query(default=30000, le=120000),
) -> DataPreviewResult | dict[str, str]:
    """Get a single row by its _phlo_row_id."""
    effective_catalog = catalog or DEFAULT_CATALOG
    effective_schema = schema or "main"

    resolved_table = (
        table
        if is_probably_qualified_table(table)
        else qualify_table_name(effective_catalog, effective_schema, table)
    )

    # Escape single quotes to prevent SQL injection
    escaped_row_id = row_id.replace("'", "''")
    query = f"SELECT * FROM {resolved_table} WHERE \"_phlo_row_id\" = '{escaped_row_id}' LIMIT 1"

    result = await execute_trino_query(
        query, effective_catalog, effective_schema, trino_url, timeout_ms
    )

    if isinstance(result, QueryExecutionError):
        return {"error": result.error}

    if not result["rows"]:
        return {"error": "Row not found"}

    return DataPreviewResult(
        columns=result["columns"],
        column_types=result["column_types"],
        rows=result["rows"],
        has_more=False,
    )
