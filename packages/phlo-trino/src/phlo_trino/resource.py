"""Trino resource for executing queries."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import time
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

    def wait_ready(
        self,
        *,
        timeout: float = 60.0,
        interval: float = 1.0,
        schema: str | None = None,
    ) -> None:
        """Wait for Trino to accept queries, retrying on startup/connection errors."""
        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        interval = max(interval, 0.0)
        while time.monotonic() < deadline:
            try:
                self.execute("SELECT 1", schema=schema)
                return
            except Exception as exc:  # noqa: BLE001 - surface real error after timeout
                if not _is_transient_trino_error(exc):
                    raise
                last_error = exc
                time.sleep(interval)
        raise TimeoutError(f"Trino not ready after {timeout:.1f}s") from last_error


def _is_transient_trino_error(exc: Exception) -> bool:
    for error in _iter_exception_chain(exc):
        message = str(error).lower()
        if "server_starting_up" in message:
            return True
        if any(
            snippet in message
            for snippet in (
                "connection refused",
                "failed to establish",
                "max retries exceeded",
                "temporarily unavailable",
                "connection reset",
                "connection aborted",
                "timed out",
            )
        ):
            return True
        errno = getattr(error, "errno", None)
        if errno in {104, 111, 113}:
            return True
        error_code = getattr(error, "error_code", None)
        if error_code:
            error_name = getattr(error_code, "name", None)
            if error_name and "server_starting_up" in str(error_name).lower():
                return True
            error_value = getattr(error_code, "code", None)
            if error_value and "server_starting_up" in str(error_value).lower():
                return True
        error_name = getattr(error, "error_name", None)
        if error_name and "server_starting_up" in str(error_name).lower():
            return True
        module_name = getattr(error.__class__, "__module__", "")
        class_name = error.__class__.__name__.lower()
        if module_name.startswith("urllib3") or module_name.startswith("requests"):
            return True
        if "connectionerror" in class_name or "connection" in class_name:
            return True
    return False


def _iter_exception_chain(exc: BaseException) -> Iterable[BaseException]:
    current: BaseException | None = exc
    while current is not None:
        yield current
        current = current.__cause__ or current.__context__
