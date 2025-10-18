from __future__ import annotations

import time
from typing import Any

import psycopg2
import psycopg2.extras

from app.config import settings


class PostgresConnector:
    """PostgreSQL database connector for marts queries."""

    def __init__(self):
        self.dsn = settings.postgres_dsn

    def execute_query(
        self, query: str, limit: int | None = None
    ) -> tuple[list[str], list[list[Any]], float]:
        """
        Execute a SQL query against Postgres.

        Returns:
            Tuple of (column_names, rows, execution_time_ms)
        """
        if limit and limit > settings.max_query_rows:
            limit = settings.max_query_rows

        if limit:
            query = f"{query} LIMIT {limit}"

        start_time = time.time()

        conn = psycopg2.connect(self.dsn)
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

    def get_glucose_readings(
        self, start_date: str | None = None, end_date: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        """Get glucose readings from marts."""
        query = "SELECT * FROM marts.mrt_glucose_overview"

        conditions = []
        if start_date:
            conditions.append(f"date >= '{start_date}'")
        if end_date:
            conditions.append(f"date <= '{end_date}'")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY date DESC"

        columns, rows, _ = self.execute_query(query, limit=limit)

        return [dict(zip(columns, row)) for row in rows]

    def get_hourly_patterns(self) -> list[dict[str, Any]]:
        """Get hourly glucose patterns from marts."""
        query = """
        SELECT
            hour_of_day,
            avg_glucose,
            readings_count
        FROM marts.mrt_glucose_hourly_patterns
        ORDER BY hour_of_day
        """

        columns, rows, _ = self.execute_query(query)
        return [dict(zip(columns, row)) for row in rows]


# Singleton instance
postgres_connector = PostgresConnector()
