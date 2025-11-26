# trino.py - Dagster resource for Trino SQL query execution with Iceberg integration
# Provides convenient helpers for executing SQL queries against Iceberg tables
# via Trino, with branch-aware catalog selection for dev/prod isolation

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Sequence

from dagster import ConfigurableResource
from trino.dbapi import Connection, Cursor, connect

from phlo.config import config


# --- Resource Classes ---
# Dagster resources for query engine integration
class TrinoResource(ConfigurableResource):
    """
    Dagster resource that exposes convenient helpers for working with Trino.

    Primarily used for running SQL against Iceberg tables and reading results
    into downstream assets.
    """

    host: str = config.trino_host
    port: int = config.trino_port
    user: str = "dagster"
    catalog: str = config.trino_catalog
    trino_schema: str | None = None
    nessie_ref: str = config.iceberg_nessie_ref

    def get_connection(self, schema: str | None = None, override_ref: str | None = None) -> Connection:
        """
        Open a Trino DB-API connection.

        Note: Nessie branching is configured at the catalog level in Trino,
        not via session properties. The iceberg catalog is configured to use
        a specific Nessie branch via iceberg.rest-catalog.prefix in the catalog
        properties file.

        Args:
            schema: Schema to use for queries
            override_ref: Override default Nessie reference (for future use)
        """
        return connect(
            host=self.host,
            port=self.port,
            user=self.user,
            catalog=self.catalog,
            schema=schema or self.trino_schema,
        )

    @contextmanager
    def connection(self, schema: str | None = None, override_ref: str | None = None) -> Iterator[Connection]:
        """
        Context manager that yields a Trino connection and ensures it gets closed.

        Args:
            schema: Schema to use for queries
            override_ref: Override default Nessie reference
        """
        conn = self.get_connection(schema=schema, override_ref=override_ref)
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def cursor(self, schema: str | None = None, override_ref: str | None = None) -> Iterator[Cursor]:
        """
        Context manager for a Trino cursor, closing both cursor and connection.

        Args:
            schema: Schema to use for queries
            override_ref: Override default Nessie reference
        """
        with self.connection(schema=schema, override_ref=override_ref) as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def execute(
        self, sql: str, parameters: Sequence[Any] | None = None, schema: str | None = None, override_ref: str | None = None
    ) -> list[tuple[Any, ...]]:
        """
        Convenience helper to execute SQL and fetch all rows.

        Args:
            sql: SQL query to execute
            parameters: Optional query parameters
            schema: Schema to use for queries
            override_ref: Override default Nessie reference

        Returns:
            List of result tuples, or empty list for statements without a result set
        """
        with self.cursor(schema=schema, override_ref=override_ref) as cursor:
            cursor.execute(sql, parameters or [])
            if cursor.description:
                return cursor.fetchall()
            return []
