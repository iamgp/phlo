"""Trino resource for executing queries."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterable

from trino.dbapi import connect

from phlo.config import get_settings

config = get_settings()


@dataclass
class TrinoResource:
    host: str | None = None
    port: int | None = None
    user: str = "dagster"
    catalog: str | None = None
    ref: str | None = None

    def _resolved_catalog(self) -> str:
        base_catalog = self.catalog or config.trino_catalog
        ref = self.ref or config.iceberg_nessie_ref
        if ref and ref != "main":
            return f"{base_catalog}_{ref}"
        return base_catalog

    def get_connection(self, schema: str | None = None):
        return connect(
            host=self.host or config.trino_host,
            port=self.port or config.trino_port,
            user=self.user,
            catalog=self._resolved_catalog(),
            schema=schema,
        )

    @contextmanager
    def cursor(self, schema: str | None = None):
        conn = self.get_connection(schema=schema)
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            try:
                cursor.close()
            finally:
                conn.close()

    def execute(self, sql: str, params: Iterable[object] | None = None, schema: str | None = None):
        params = list(params or [])
        with self.cursor(schema=schema) as cursor:
            cursor.execute(sql, params)
            if cursor.description is None:
                return []
            return cursor.fetchall()
