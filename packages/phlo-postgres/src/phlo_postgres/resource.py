"""Postgres resource for publishing and operational writes."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

import psycopg2

from phlo.logging import get_logger
from phlo_postgres.settings import get_settings

logger = get_logger(__name__)


@dataclass
class PostgresResource:
    """Lightweight Postgres connection resource."""

    host: str | None = None
    port: int | None = None
    user: str | None = None
    password: str | None = None
    database: str | None = None
    _connection: Any | None = field(default=None, init=False, repr=False)

    def __enter__(self) -> "PostgresResource":
        """Open a connection for context-managed usage.

        Returns:
            PostgresResource: The initialized resource instance.
        """
        self._ensure_connection()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """Close the resource on context exit.

        Args:
            exc_type: Exception type raised in the context, if any.
            exc: Exception instance raised in the context, if any.
            tb: Traceback object for the raised exception, if any.
        """
        if exc_type is not None:
            try:
                self.rollback()
            except Exception:  # noqa: BLE001 - best effort rollback on context exit
                logger.warning("postgres_resource_rollback_failed", exc_info=True)
                pass
        self.close()

    def __del__(self) -> None:
        """Best-effort connection cleanup during object destruction."""
        try:
            self.close()
        except Exception:  # noqa: BLE001 - destructor must never raise
            logger.debug("postgres_resource_close_on_del_failed", exc_info=True)
            pass

    def _ensure_connection(self):
        """Create and cache a psycopg2 connection when needed.

        Returns:
            Any: Active psycopg2 connection object.
        """
        if self._connection is None or getattr(self._connection, "closed", 1):
            settings = get_settings()
            host = self.host or settings.postgres_host
            port = self.port or settings.postgres_port
            database = self.database or settings.postgres_db
            start = perf_counter()
            logger.info(
                "postgres_resource_connection_started",
                host=host,
                port=port,
                database=database,
            )
            try:
                self._connection = psycopg2.connect(
                    host=host,
                    port=port,
                    user=self.user or settings.postgres_user,
                    password=self.password or settings.postgres_password,
                    dbname=database,
                )
            except Exception:
                logger.error(
                    "postgres_resource_connection_failed",
                    host=host,
                    port=port,
                    database=database,
                    elapsed_ms=round((perf_counter() - start) * 1000, 2),
                    exc_info=True,
                )
                raise
            logger.info(
                "postgres_resource_connection_completed",
                host=host,
                port=port,
                database=database,
                elapsed_ms=round((perf_counter() - start) * 1000, 2),
            )
        return self._connection

    @contextmanager
    def cursor(self):
        """Yield a cursor; caller owns transaction commit/rollback."""

        connection = self._ensure_connection()
        cursor = connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    @contextmanager
    def transactional_cursor(self):
        """Yield a cursor and commit/rollback automatically."""

        connection = self._ensure_connection()
        cursor = connection.cursor()
        start = perf_counter()
        logger.info("postgres_transaction_started")
        try:
            yield cursor
        except Exception:
            logger.warning(
                "postgres_transaction_rollback",
                elapsed_ms=round((perf_counter() - start) * 1000, 2),
                exc_info=True,
            )
            connection.rollback()
            raise
        else:
            connection.commit()
            logger.info(
                "postgres_transaction_committed",
                elapsed_ms=round((perf_counter() - start) * 1000, 2),
            )
        finally:
            cursor.close()

    def commit(self) -> None:
        """Commit the current transaction."""
        start = perf_counter()
        self._ensure_connection().commit()
        logger.info(
            "postgres_commit_completed",
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
        )

    def rollback(self) -> None:
        """Roll back the current transaction."""
        start = perf_counter()
        self._ensure_connection().rollback()
        logger.info(
            "postgres_rollback_completed",
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
        )

    def close(self) -> None:
        """Close and clear the cached database connection."""
        if self._connection is not None and not getattr(self._connection, "closed", 1):
            start = perf_counter()
            logger.info("postgres_resource_connection_close_started")
            try:
                self._connection.close()
            except Exception:
                logger.warning("postgres_resource_connection_close_failed", exc_info=True)
                raise
            logger.info(
                "postgres_resource_connection_close_completed",
                elapsed_ms=round((perf_counter() - start) * 1000, 2),
            )
        self._connection = None
