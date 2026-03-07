"""Iceberg Catalog API Router.

Endpoints for querying Iceberg tables via Trino.
Provides table listing, schema info, and metadata.
"""

from __future__ import annotations

import time
from typing import Any, Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from phlo.logging import get_logger
from phlo_api.observatory_api.trino import (
    QueryExecutionError,
    execute_trino_query,
    quote_identifier,
    resolve_default_catalog,
)

logger = get_logger(__name__)

router = APIRouter(tags=["iceberg"])

# Simple in-memory cache (can be replaced with Redis later)
_cache: dict[str, tuple[float, Any]] = {}
CACHE_TTL_TABLES = 60.0  # 1 minute
CACHE_TTL_SCHEMA = 300.0  # 5 minutes


def _cache_get(key: str, ttl: float) -> Any | None:
    """Get a cached value when still valid.

    Args:
        key: Cache key.
        ttl: Time-to-live in seconds.

    Returns:
        Cached value or `None` when missing/expired.
    """
    entry = _cache.get(key)
    if not entry:
        return None
    timestamp, value = entry
    if time.time() - timestamp > ttl:
        _cache.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: Any) -> None:
    """Store a value in the in-memory cache.

    Args:
        key: Cache key.
        value: Value to cache.
    """
    _cache[key] = (time.time(), value)


# --- Pydantic Models ---

Layer = Literal["bronze", "silver", "gold", "publish", "unknown"]


class IcebergTable(BaseModel):
    """Represents an Iceberg table exposed by Trino.

    Attributes:
        catalog: Trino catalog name.
        schema_name: Trino schema name.
        name: Table name.
        full_name: Fully qualified table identifier.
        layer: Inferred medallion layer classification.
    """

    catalog: str
    schema_name: str  # 'schema' is reserved in Pydantic
    name: str
    full_name: str
    layer: Layer


class TableColumn(BaseModel):
    """Represents a column in a table schema.

    Attributes:
        name: Column name.
        type: SQL type string.
        nullable: Whether the column allows NULL values.
        comment: Optional column comment from catalog metadata.
    """

    name: str
    type: str
    nullable: bool
    comment: str | None = None


class TableMetadata(BaseModel):
    """Represents table metadata for observatory responses.

    Attributes:
        table: Table descriptor.
        columns: Table column definitions.
        row_count: Optional row count when available.
        last_modified: Optional last-modified timestamp when available.
    """

    table: IcebergTable
    columns: list[TableColumn]
    row_count: int | None = None
    last_modified: str | None = None


# --- Layer Inference ---


def infer_layer(name: str) -> Layer:
    """Infer data layer from table name.

    Args:
        name: Table name.

    Returns:
        Inferred medallion layer.
    """
    lower = name.lower()
    # Bronze: raw ingestion tables from DLT
    if lower.startswith("dlt_"):
        return "bronze"
    # Silver: staged/cleaned tables
    if lower.startswith("stg_"):
        return "silver"
    # Gold: curated fact/dimension tables
    if lower.startswith("fct_") or lower.startswith("dim_"):
        return "gold"
    # Publish: mart tables for BI consumption
    if lower.startswith("mrt_") or lower.startswith("publish_"):
        return "publish"
    # Fallback checks
    if "raw" in lower:
        return "bronze"
    if "staging" in lower:
        return "silver"
    return "unknown"


def infer_layer_from_schema(schema: str, table_name: str) -> Layer:
    """Infer data layer from table and schema names.

    Args:
        schema: Schema name.
        table_name: Table name.

    Returns:
        Inferred medallion layer.
    """
    # First try table name (most reliable)
    from_table = infer_layer(table_name)
    if from_table != "unknown":
        return from_table

    # Fall back to schema name
    s = schema.lower()
    if s in ("bronze", "raw"):
        return "bronze"
    if s in ("silver", "staging"):
        return "silver"
    if s in ("gold", "curated"):
        return "gold"
    if s in ("publish", "marts"):
        return "publish"

    return "unknown"


# --- Table Fetching ---


async def fetch_tables(
    branch: str,
    catalog: str,
    preferred_schema: str | None,
    trino_url: str | None,
    timeout_ms: int,
) -> list[IcebergTable] | dict[str, str]:
    """Fetch tables from known Iceberg schemas.

    Args:
        branch: Branch/schema fallback name.
        catalog: Trino catalog name.
        preferred_schema: Optional schema to prioritize.
        trino_url: Optional Trino URL override.
        timeout_ms: Query timeout in milliseconds.

    Returns:
        Table list or an error dictionary.
    """
    schemas_to_query = ["bronze", "silver", "gold", "raw", "marts", "publish"]

    # Prioritize preferred schema
    if preferred_schema and preferred_schema in schemas_to_query:
        schemas_to_query = [preferred_schema] + [
            s for s in schemas_to_query if s != preferred_schema
        ]

    all_tables: list[IcebergTable] = []
    seen_tables: set[str] = set()
    errors: list[str] = []

    for schema in schemas_to_query:
        sql = f"SHOW TABLES FROM {quote_identifier(catalog)}.{quote_identifier(schema)}"
        result = await execute_trino_query(sql, catalog, schema, trino_url, timeout_ms)

        if isinstance(result, QueryExecutionError):
            errors.append(f"{schema}: {result.error}")
            continue

        for row in result["rows"]:
            table_name = row.get("Table") or row.get("table_name") or row.get("tableName")
            if table_name and table_name not in seen_tables:
                seen_tables.add(table_name)
                all_tables.append(
                    IcebergTable(
                        catalog=catalog,
                        schema_name=schema,
                        name=table_name,
                        full_name=f"{quote_identifier(catalog)}.{quote_identifier(schema)}.{quote_identifier(table_name)}",
                        layer=infer_layer_from_schema(schema, table_name),
                    )
                )

    # If no tables found in standard schemas, try branch as schema
    if not all_tables and errors:
        # Try branch as the schema name
        sql = f"SHOW TABLES FROM {quote_identifier(catalog)}.{quote_identifier(branch)}"
        result = await execute_trino_query(sql, catalog, branch, trino_url, timeout_ms)

        if isinstance(result, QueryExecutionError):
            return {"error": "; ".join(errors)}

        for row in result["rows"]:
            table_name = row.get("Table") or row.get("table_name") or row.get("tableName")
            if table_name:
                all_tables.append(
                    IcebergTable(
                        catalog=catalog,
                        schema_name=branch,
                        name=table_name,
                        full_name=f"{quote_identifier(catalog)}.{quote_identifier(branch)}.{quote_identifier(table_name)}",
                        layer=infer_layer(table_name),
                    )
                )

    if not all_tables and errors:
        return {"error": "; ".join(errors)}

    # Sort by layer then name
    layer_order = {"bronze": 0, "silver": 1, "gold": 2, "publish": 3, "unknown": 4}
    all_tables.sort(key=lambda t: (layer_order[t.layer], t.name))

    return all_tables


async def fetch_table_schema(
    table: str,
    schema: str,
    catalog: str,
    trino_url: str | None = None,
    timeout_ms: int = 30000,
) -> list[TableColumn] | dict[str, str]:
    """Fetch table columns from Trino.

    Args:
        table: Table name.
        schema: Schema name.
        catalog: Trino catalog name.
        trino_url: Optional Trino URL override.
        timeout_ms: Query timeout in milliseconds.

    Returns:
        Column list or an error dictionary.
    """
    sql = (
        f"DESCRIBE {quote_identifier(catalog)}.{quote_identifier(schema)}.{quote_identifier(table)}"
    )
    result = await execute_trino_query(sql, catalog, schema, trino_url, timeout_ms)

    if isinstance(result, QueryExecutionError):
        return {"error": result.error}

    columns = []
    for row in result["rows"]:
        col_name = row.get("Column") or row.get("column_name")
        col_type = row.get("Type") or row.get("data_type") or "unknown"
        extra = row.get("Extra") or ""
        comment = row.get("Comment") or None

        if col_name:
            columns.append(
                TableColumn(
                    name=col_name,
                    type=col_type,
                    nullable="NOT NULL" not in extra.upper() if extra else True,
                    comment=comment if comment else None,
                )
            )

    return columns


# --- API Endpoints ---


@router.get("/tables", response_model=list[IcebergTable] | dict)
async def get_tables(
    branch: str = "main",
    catalog: str | None = None,
    preferred_schema: str | None = None,
    trino_url: str | None = None,
    timeout_ms: int = Query(default=30000, le=120000),
) -> list[IcebergTable] | dict[str, str]:
    """Get tables from the Iceberg catalog.

    Args:
        branch: Branch/schema fallback name.
        catalog: Optional Trino catalog override.
        preferred_schema: Optional schema to prioritize.
        trino_url: Optional Trino URL override.
        timeout_ms: Query timeout in milliseconds.

    Returns:
        Table list or an error dictionary.
    """
    effective_catalog = catalog or resolve_default_catalog()

    cache_key = f"tables:{effective_catalog}:{branch}:{preferred_schema}:{trino_url or 'default'}"
    cached = _cache_get(cache_key, CACHE_TTL_TABLES)
    if cached is not None:
        return cached

    result = await fetch_tables(branch, effective_catalog, preferred_schema, trino_url, timeout_ms)
    if not isinstance(result, dict):
        _cache_set(cache_key, result)
    return result


@router.get("/tables/{table:path}/schema", response_model=list[TableColumn] | dict)
async def get_table_schema(
    table: str,
    schema: str | None = None,
    branch: str = "main",
    catalog: str | None = None,
    trino_url: str | None = None,
    timeout_ms: int = Query(default=30000, le=120000),
) -> list[TableColumn] | dict[str, str]:
    """Get table column schema.

    Args:
        table: Table name.
        schema: Optional schema override.
        branch: Default schema/branch.
        catalog: Optional Trino catalog override.
        trino_url: Optional Trino URL override.
        timeout_ms: Query timeout in milliseconds.

    Returns:
        Column list or an error dictionary.
    """
    effective_catalog = catalog or resolve_default_catalog()
    effective_schema = schema or branch

    cache_key = f"schema:{effective_catalog}:{effective_schema}:{table}:{trino_url or 'default'}"
    cached = _cache_get(cache_key, CACHE_TTL_SCHEMA)
    if cached is not None:
        return cached

    result = await fetch_table_schema(
        table, effective_schema, effective_catalog, trino_url, timeout_ms
    )
    if not isinstance(result, dict):
        _cache_set(cache_key, result)
    return result


@router.get("/tables/{table:path}/row-count", response_model=int | dict)
async def get_table_row_count(
    table: str,
    branch: str = "main",
    catalog: str | None = None,
    trino_url: str | None = None,
    timeout_ms: int = Query(default=30000, le=120000),
) -> int | dict[str, str]:
    """Get row count for a table.

    Args:
        table: Table name.
        branch: Schema/branch name.
        catalog: Optional Trino catalog override.
        trino_url: Optional Trino URL override.
        timeout_ms: Query timeout in milliseconds.

    Returns:
        Row count or an error dictionary.
    """
    effective_catalog = catalog or resolve_default_catalog()
    sql = f"SELECT COUNT(*) as cnt FROM {quote_identifier(effective_catalog)}.{quote_identifier(branch)}.{quote_identifier(table)}"

    result = await execute_trino_query(sql, effective_catalog, branch, trino_url, timeout_ms)

    if isinstance(result, QueryExecutionError):
        return {"error": result.error}

    if result["rows"]:
        return int(result["rows"][0].get("cnt", 0))
    return 0


@router.get("/tables/{table:path}/metadata", response_model=TableMetadata | dict)
async def get_table_metadata(
    table: str,
    branch: str = "main",
    catalog: str | None = None,
    trino_url: str | None = None,
    timeout_ms: int = Query(default=30000, le=120000),
) -> TableMetadata | dict[str, str]:
    """Get table metadata including schema and optional row count.

    Args:
        table: Table name.
        branch: Schema/branch name.
        catalog: Optional Trino catalog override.
        trino_url: Optional Trino URL override.
        timeout_ms: Query timeout in milliseconds.

    Returns:
        Table metadata or an error dictionary.
    """
    effective_catalog = catalog or resolve_default_catalog()

    # Get schema
    schema_result = await fetch_table_schema(
        table, branch, effective_catalog, trino_url, timeout_ms
    )
    if isinstance(schema_result, dict) and "error" in schema_result:
        return schema_result

    # Get row count (optional)
    row_count = None
    try:
        count_result = await get_table_row_count(
            table, branch, effective_catalog, trino_url, timeout_ms
        )
        if isinstance(count_result, int):
            row_count = count_result
    except Exception:
        pass  # Row count is optional

    return TableMetadata(
        table=IcebergTable(
            catalog=effective_catalog,
            schema_name=branch,
            name=table,
            full_name=f"{quote_identifier(effective_catalog)}.{quote_identifier(branch)}.{quote_identifier(table)}",
            layer=infer_layer(table),
        ),
        columns=schema_result,  # type: ignore
        row_count=row_count,
    )
