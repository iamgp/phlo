"""Postgres resource for publishing and operational writes."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from psycopg2 import pool, sql

from phlo.logging import get_logger
from phlo_postgres.settings import get_settings

logger = get_logger(__name__)


@dataclass
class PostgresResource:
    """Lightweight Postgres connection resource with connection pooling."""

    host: str | None = None
    port: int | None = None
    user: str | None = None
    password: str | None = None
    database: str | None = None
    min_connections: int = 1
    max_connections: int = 5
    _pool: pool.SimpleConnectionPool | None = field(default=None, init=False, repr=False)
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
        try:
            self.close()
        finally:
            self.close_pool()

    def __del__(self) -> None:
        """Best-effort connection and pool cleanup during object destruction."""
        try:
            self.close()
        except Exception:  # noqa: BLE001 - destructor must never raise
            logger.debug("postgres_resource_close_on_del_failed", exc_info=True)
        try:
            self.close_pool()
        except Exception:  # noqa: BLE001 - destructor must never raise
            logger.debug("postgres_resource_pool_close_on_del_failed", exc_info=True)

    def _ensure_pool(self) -> pool.SimpleConnectionPool:
        """Create the connection pool if it does not already exist.

        Returns:
            pool.SimpleConnectionPool: The active connection pool.
        """
        if self._pool is None or self._pool.closed:
            settings = get_settings()
            host = self.host or settings.postgres_host
            port = self.port or settings.postgres_port
            database = self.database or settings.postgres_db
            start = perf_counter()
            logger.info(
                "postgres_pool_creation_started",
                host=host,
                port=port,
                database=database,
                min_connections=self.min_connections,
                max_connections=self.max_connections,
            )
            try:
                self._pool = pool.SimpleConnectionPool(
                    minconn=self.min_connections,
                    maxconn=self.max_connections,
                    host=host,
                    port=port,
                    user=self.user or settings.postgres_user,
                    password=self.password or settings.postgres_password,
                    dbname=database,
                )
            except Exception:
                logger.error(
                    "postgres_pool_creation_failed",
                    host=host,
                    port=port,
                    database=database,
                    elapsed_ms=round((perf_counter() - start) * 1000, 2),
                    exc_info=True,
                )
                raise
            logger.info(
                "postgres_pool_creation_completed",
                host=host,
                port=port,
                database=database,
                elapsed_ms=round((perf_counter() - start) * 1000, 2),
            )
        return self._pool

    def _ensure_connection(self):
        """Get a connection from the pool, creating the pool if needed.

        Returns:
            Any: Active psycopg2 connection object.
        """
        if self._connection is None or getattr(self._connection, "closed", 1):
            connection_pool = self._ensure_pool()
            # Return the stale connection slot before acquiring a new one
            if self._connection is not None:
                try:
                    connection_pool.putconn(self._connection, close=True)
                except Exception:  # noqa: BLE001 - best effort return
                    logger.debug("postgres_resource_stale_connection_return_failed", exc_info=True)
                self._connection = None
            start = perf_counter()
            logger.info("postgres_resource_connection_started")
            try:
                self._connection = connection_pool.getconn()
            except Exception:
                logger.error(
                    "postgres_resource_connection_failed",
                    elapsed_ms=round((perf_counter() - start) * 1000, 2),
                    exc_info=True,
                )
                raise
            logger.info(
                "postgres_resource_connection_completed",
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
        """Return the current connection to the pool."""
        if self._connection is not None and self._pool is not None:
            start = perf_counter()
            logger.info("postgres_resource_connection_return_started")
            try:
                self._pool.putconn(self._connection)
            except Exception:
                logger.warning("postgres_resource_connection_return_failed", exc_info=True)
                raise
            logger.info(
                "postgres_resource_connection_return_completed",
                elapsed_ms=round((perf_counter() - start) * 1000, 2),
            )
        self._connection = None

    def close_pool(self) -> None:
        """Tear down the connection pool entirely."""
        if self._pool is not None and not self._pool.closed:
            start = perf_counter()
            logger.info("postgres_pool_close_started")
            try:
                self._pool.closeall()
            except Exception:
                logger.warning("postgres_pool_close_failed", exc_info=True)
                raise
            logger.info(
                "postgres_pool_close_completed",
                elapsed_ms=round((perf_counter() - start) * 1000, 2),
            )
        self._pool = None

    def is_healthy(self) -> bool:
        """Check if the database connection is alive."""
        try:
            conn = self._ensure_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception:
            logger.warning("postgres_health_check_failed", exc_info=True)
            return False

    def execute(self, sql_stmt: str, params: tuple | None = None) -> None:
        """Execute a SQL statement (no return value)."""
        start = perf_counter()
        logger.info("postgres_execute_started")
        with self.cursor() as cur:
            cur.execute(sql_stmt, params)
        self.commit()
        logger.info(
            "postgres_execute_completed",
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
        )

    def query(self, sql_stmt: str, params: tuple | None = None) -> list[tuple]:
        """Execute a SQL query and return all rows."""
        start = perf_counter()
        logger.info("postgres_query_started")
        with self.cursor() as cur:
            cur.execute(sql_stmt, params)
            rows = cur.fetchall()
        logger.info(
            "postgres_query_completed",
            row_count=len(rows),
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
        )
        return rows

    def query_one(self, sql_stmt: str, params: tuple | None = None) -> tuple | None:
        """Execute a SQL query and return the first row."""
        start = perf_counter()
        logger.info("postgres_query_one_started")
        with self.cursor() as cur:
            cur.execute(sql_stmt, params)
            row = cur.fetchone()
        logger.info(
            "postgres_query_one_completed",
            has_result=row is not None,
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
        )
        return row

    def ensure_schema(self, schema_name: str) -> None:
        """Create a schema if it does not exist."""
        with self.transactional_cursor() as cur:
            cur.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema_name))
            )
        logger.info("postgres_schema_ensured", schema_name=schema_name)
