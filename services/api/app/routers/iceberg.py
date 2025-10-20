# iceberg.py - FastAPI router for Iceberg table access via Trino
# Provides REST endpoints to query and explore Iceberg tables
# with caching and security controls

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.auth.dependencies import CurrentUser
from app.config import settings
from app.connectors.trino import trino_connector
from app.middleware.cache import cached
from app.models.schemas import IcebergTable

# --- Router Configuration ---
# Iceberg data access router
router = APIRouter(prefix="/iceberg", tags=["Iceberg Data Access"])


# --- Iceberg Data Endpoints ---
# REST API endpoints for Iceberg table exploration
@router.get("/tables", response_model=list[IcebergTable], summary="List all Iceberg tables")
@cached(ttl=settings.cache_iceberg_queries_ttl)
async def list_tables(
    current_user: CurrentUser,
    schema: str | None = Query(None, description="Filter by schema (raw, bronze, silver, gold)"),
) -> list[IcebergTable]:
    """
    List all Iceberg tables across all schemas or filtered by schema.

    Cached for 30 minutes.
    """
    if schema:
        schemas = [schema]
    else:
        # List all schemas
        try:
            all_schemas = trino_connector.list_schemas()
            # Filter to relevant schemas (exclude system schemas)
            schemas = [s for s in all_schemas if s in ["raw", "bronze", "silver", "gold", "marts"]]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list schemas: {str(e)}",
            )

    tables = []
    for schema_name in schemas:
        try:
            schema_tables = trino_connector.list_tables(schema_name)
            tables.extend(
                [
                    IcebergTable(schema_name=t["schema_name"], table_name=t["table_name"])
                    for t in schema_tables
                ]
            )
        except Exception:
            # Skip schemas that don't exist or can't be accessed
            continue

    return tables


@router.get("/{schema}/{table}", summary="Query an Iceberg table")
@cached(ttl=settings.cache_iceberg_queries_ttl)
async def query_table(
    current_user: CurrentUser,
    schema: str,
    table: str,
    filter: str | None = Query(None, description="SQL WHERE clause (without 'WHERE')"),
    order_by: str | None = Query(None, description="SQL ORDER BY clause (without 'ORDER BY')"),
    limit: int = Query(1000, le=10000, description="Maximum number of rows"),
) -> dict[str, Any]:
    """
    Query data from an Iceberg table via Trino.

    Cached for 30 minutes. Supports filtering and ordering.

    Example:
        GET /iceberg/bronze/stg_entries?filter=date>='2024-01-01'&limit=100
    """
    # Build query
    query = f"SELECT * FROM {settings.trino_catalog}.{schema}.{table}"

    if filter:
        # Basic SQL injection protection - reject certain keywords
        dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "CREATE", "ALTER", "EXEC"]
        if any(keyword in filter.upper() for keyword in dangerous_keywords):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filter: contains dangerous SQL keywords",
            )
        query += f" WHERE {filter}"

    if order_by:
        query += f" ORDER BY {order_by}"

    try:
        columns, rows, execution_time_ms = trino_connector.execute_query(query, limit=limit)

        return {
            "schema": schema,
            "table": table,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "execution_time_ms": execution_time_ms,
            "cached": True,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}",
        )
