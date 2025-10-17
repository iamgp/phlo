from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Sequence

from dagster import ConfigurableResource
from trino.dbapi import Connection, Cursor, connect

from cascade.config import config


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

    def get_connection(self, schema: str | None = None) -> Connection:
        """Open a Trino DB-API connection."""
        return connect(
            host=self.host,
            port=self.port,
            user=self.user,
            catalog=self.catalog,
            schema=schema or self.trino_schema,
        )

    @contextmanager
    def connection(self, schema: str | None = None) -> Iterator[Connection]:
        """Context manager that yields a Trino connection and ensures it gets closed."""
        conn = self.get_connection(schema=schema)
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def cursor(self, schema: str | None = None) -> Iterator[Cursor]:
        """Context manager for a Trino cursor, closing both cursor and connection."""
        with self.connection(schema=schema) as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def execute(
        self, sql: str, parameters: Sequence[Any] | None = None, schema: str | None = None
    ) -> list[tuple[Any, ...]]:
        """
        Convenience helper to execute SQL and fetch all rows.

        Returns an empty list for statements without a result set.
        """
        with self.cursor(schema=schema) as cursor:
            cursor.execute(sql, parameters or [])
            if cursor.description:
                return cursor.fetchall()
            return []
