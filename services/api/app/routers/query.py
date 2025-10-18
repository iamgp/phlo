
from fastapi import APIRouter, HTTPException, status

from app.auth.dependencies import AdminUser
from app.connectors.postgres import postgres_connector
from app.connectors.trino import trino_connector
from app.models.schemas import QueryRequest, QueryResponse

router = APIRouter(prefix="/query", tags=["Advanced Queries"])


@router.post("/sql", response_model=QueryResponse, summary="Execute SQL query (admin only)")
async def execute_sql(
    admin_user: AdminUser,
    request: QueryRequest,
) -> QueryResponse:
    """
    Execute arbitrary SQL query against Trino or Postgres.

    **Admin only** - requires admin role.

    Security:
    - Read-only queries recommended
    - Query timeout enforced (30s)
    - Row limit enforced (10,000 max)
    """
    # Basic SQL injection protection - reject certain keywords
    dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "CREATE", "ALTER", "EXEC", "GRANT"]
    query_upper = request.query.upper()

    if any(keyword in query_upper for keyword in dangerous_keywords):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query contains dangerous SQL keywords (write operations not allowed)",
        )

    try:
        if request.engine == "trino":
            columns, rows, execution_time_ms = trino_connector.execute_query(
                request.query, limit=request.limit
            )
        else:  # postgres
            columns, rows, execution_time_ms = postgres_connector.execute_query(
                request.query, limit=request.limit
            )

        return QueryResponse(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=execution_time_ms,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}",
        )
