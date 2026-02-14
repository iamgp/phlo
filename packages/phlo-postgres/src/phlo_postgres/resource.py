"""Postgres resource for publishing and operational writes."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import psycopg2

from phlo_postgres.settings import get_settings


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
        self._ensure_connection()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is not None:
            try:
                self.rollback()
            except Exception:  # noqa: BLE001 - best effort rollback on context exit
                pass
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:  # noqa: BLE001 - destructor must never raise
            pass

    def _ensure_connection(self):
        if self._connection is None or getattr(self._connection, "closed", 1):
            settings = get_settings()
            self._connection = psycopg2.connect(
                host=self.host or settings.postgres_host,
                port=self.port or settings.postgres_port,
                user=self.user or settings.postgres_user,
                password=self.password or settings.postgres_password,
                dbname=self.database or settings.postgres_db,
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
        try:
            yield cursor
        except Exception:
            connection.rollback()
            raise
        else:
            connection.commit()
        finally:
            cursor.close()

    def commit(self) -> None:
        self._ensure_connection().commit()

    def rollback(self) -> None:
        self._ensure_connection().rollback()

    def close(self) -> None:
        if self._connection is not None and not getattr(self._connection, "closed", 1):
            self._connection.close()
        self._connection = None
