
import time
from typing import Any

import trino

from app.config import settings


class TrinoConnector:
    """Trino database connector for Iceberg queries."""

    def __init__(self):
        self.host = settings.trino_host
        self.port = settings.trino_port
        self.catalog = settings.trino_catalog
        self.user = settings.trino_user

    def execute_query(
        self, query: str, limit: int | None = None, timeout: int | None = None
    ) -> tuple[list[str], list[list[Any]], float]:
        """
        Execute a SQL query against Trino.

        Returns:
            Tuple of (column_names, rows, execution_time_ms)
        """
        if limit and limit > settings.max_query_rows:
            limit = settings.max_query_rows

        if limit:
            query = f"{query} LIMIT {limit}"

        timeout = timeout or settings.query_timeout_seconds

        start_time = time.time()

        conn = trino.dbapi.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            catalog=self.catalog,
            http_scheme="http",
        )

        cursor = conn.cursor()

        try:
            cursor.execute(query)

            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Fetch rows
            rows = cursor.fetchall()

            execution_time_ms = (time.time() - start_time) * 1000

            return columns, rows, execution_time_ms

        finally:
            cursor.close()
            conn.close()

    def list_tables(self, schema: str) -> list[dict[str, str]]:
        """List all tables in a schema."""
        query = f"SHOW TABLES FROM {self.catalog}.{schema}"
        columns, rows, _ = self.execute_query(query)

        tables = []
        for row in rows:
            tables.append(
                {
                    "schema_name": schema,
                    "table_name": row[0],
                }
            )
        return tables

    def list_schemas(self) -> list[str]:
        """List all schemas in the catalog."""
        query = f"SHOW SCHEMAS FROM {self.catalog}"
        columns, rows, _ = self.execute_query(query)
        return [row[0] for row in rows]


# Singleton instance
trino_connector = TrinoConnector()
