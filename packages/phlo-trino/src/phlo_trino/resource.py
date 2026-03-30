"""Trino resource for executing queries and managing connections.

This module provides the TrinoResource class for interacting with Trino,
including connection management, query execution, and wait-for-readiness
functionality with automatic retry logic.

Classes:
    TrinoResource: Resource wrapper for Trino connections and queries.
    _ConfigFacade: Backward-compatible config shim for test patching.

Constants:
    TRINO_QUERY_ENGINE_SUPPORT: Capability support flags for query engine.

Functions:
    _is_transient_trino_error: Check if an exception indicates transient error.
    _iter_exception_chain: Yield exception and its chained causes.

Example:
    >>> from phlo_trino.resource import TrinoResource
    >>> trino = TrinoResource()
    >>> results = trino.execute("SELECT * FROM iceberg.my_schema.my_table")
    >>> trino.wait_ready(timeout=30.0)

"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import time
from typing import Iterable

from trino.dbapi import connect

from phlo.capabilities import CapabilitySupport, RuntimeContext, resolve_runtime_ref
from phlo.logging import get_logger
from phlo_trino.settings import get_settings as get_trino_settings

logger = get_logger(__name__)

TRINO_QUERY_ENGINE_SUPPORT = CapabilitySupport(
    supports_refs=True,
    supports_time_travel=True,
)


class _ConfigFacade:
    """Backward-compatible config shim for tests patching `phlo_trino.resource.config`."""

    @property
    def trino_host(self) -> str:
        """Get the configured Trino host.

        Returns:
            Trino service hostname.

        """
        return get_trino_settings().trino_host

    @property
    def trino_port(self) -> int:
        """Get the configured Trino port.

        Returns:
            Trino HTTP port.

        """
        return get_trino_settings().trino_port

    @property
    def trino_catalog(self) -> str:
        """Get the configured Trino catalog.

        Returns:
            Default Trino catalog name.

        """
        return get_trino_settings().trino_catalog

    @property
    def default_catalog_ref(self) -> str:
        """Get the configured default ref for ref-aware catalogs.

        Returns:
            Branch or tag reference.

        """
        return get_trino_settings().trino_default_ref


config = _ConfigFacade()


@dataclass
class TrinoResource:
    """Resource wrapper for Trino connections and query execution.

    Attributes:
        host: Optional Trino host override.
        port: Optional Trino port override.
        user: Trino username for connections.
        catalog: Optional catalog override.
        ref: Optional Nessie ref override for catalog resolution.
        runtime: Optional runtime context providing canonical ref routing.

    """

    host: str | None = None
    port: int | None = None
    user: str = "dagster"
    catalog: str | None = None
    ref: str | None = None
    runtime: RuntimeContext | None = None

    def _resolved_ref(self) -> str | None:
        """Resolve the effective ref for Trino catalog routing.

        Returns:
            Resolved reference string or None if using default.

        """
        return resolve_runtime_ref(
            self.runtime,
            support=TRINO_QUERY_ENGINE_SUPPORT,
            default_ref=self.ref or config.default_catalog_ref,
        )

    def _resolved_catalog(self) -> str:
        """Resolve the catalog name, including non-main Nessie refs.

        Returns:
            Catalog name used for Trino connections.

        """
        base_catalog = self.catalog or config.trino_catalog
        ref = self._resolved_ref()
        if ref and ref != "main":
            return f"{base_catalog}_{ref}"
        return base_catalog

    def get_connection(self, schema: str | None = None):
        """Create a DB-API connection to Trino.

        Args:
            schema: Optional schema name for the connection.

        Returns:
            Open Trino DB-API connection.

        """
        return connect(
            host=self.host or config.trino_host,
            port=self.port or config.trino_port,
            user=self.user,
            catalog=self._resolved_catalog(),
            schema=schema,
        )

    @contextmanager
    def cursor(self, schema: str | None = None):
        """Yield a Trino cursor and close resources on exit.

        Args:
            schema: Optional schema name for the connection.

        Yields:
            Active Trino cursor.

        """
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
        """Execute SQL and return query results when present.

        Args:
            sql: SQL statement to execute.
            params: Optional positional query parameters.
            schema: Optional schema name for the connection.

        Returns:
            List of query result rows, or an empty list for statements without results.

        """
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
        """Wait for Trino to accept queries, retrying on startup/connection errors.

        Polls Trino with "SELECT 1" until successful or timeout exceeded.
        Automatically retries on transient connection errors.

        Args:
            timeout: Maximum seconds to wait before raising TimeoutError.
            interval: Seconds between retry attempts.
            schema: Optional schema name for the test query.

        Raises:
            TimeoutError: If Trino is not ready within the timeout period.
            Exception: If a non-transient error occurs.

        Example:
            >>> trino = TrinoResource()
            >>> trino.wait_ready(timeout=30.0, interval=2.0)

        """
        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        interval = max(interval, 0.0)
        while time.monotonic() < deadline:
            try:
                self.execute("SELECT 1", schema=schema)
                logger.info(
                    "trino_wait_ready_succeeded",
                    host=self.host or config.trino_host,
                    port=self.port or config.trino_port,
                    schema=schema,
                )
                return
            except Exception as exc:  # noqa: BLE001 - surface real error after timeout
                if not _is_transient_trino_error(exc):
                    logger.exception(
                        "trino_wait_ready_non_transient_error",
                        host=self.host or config.trino_host,
                        port=self.port or config.trino_port,
                        schema=schema,
                    )
                    raise
                last_error = exc
                logger.debug(
                    "trino_wait_ready_retry",
                    host=self.host or config.trino_host,
                    port=self.port or config.trino_port,
                    schema=schema,
                    retry_interval_seconds=interval,
                )
                time.sleep(interval)
        logger.error(
            "trino_wait_ready_timeout",
            host=self.host or config.trino_host,
            port=self.port or config.trino_port,
            schema=schema,
            timeout_seconds=timeout,
        )
        raise TimeoutError(f"Trino not ready after {timeout:.1f}s") from last_error


def _is_transient_trino_error(exc: Exception) -> bool:
    """Check whether an exception chain indicates transient Trino startup/connectivity errors.

    Args:
        exc: Root exception to inspect.

    Returns:
        True when retrying is likely useful; otherwise False.

    """
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
    """Yield an exception and its chained causes/contexts.

    Args:
        exc: Starting exception.

    Yields:
        Exception objects from the chain, root first.

    """
    current: BaseException | None = exc
    while current is not None:
        yield current
        current = current.__cause__ or current.__context__
