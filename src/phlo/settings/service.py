"""Postgres-backed settings store."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from typing import Any

import psycopg2
from jsonschema import ValidationError, validate

from phlo.config import get_settings


class SettingsScope(StrEnum):
    GLOBAL = "global"
    EXTENSION = "extension"


@dataclass(frozen=True)
class SettingsRecord:
    scope: SettingsScope
    namespace: str
    settings: dict[str, Any]
    updated_at: str | None


class SettingsService:
    """Settings service with optional schema validation."""

    def __init__(self, db_url: str) -> None:
        self._db_url = db_url

    def get(self, scope: SettingsScope, namespace: str) -> SettingsRecord | None:
        with psycopg2.connect(self._db_url) as conn:
            self._ensure_table(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT settings, updated_at
                    FROM phlo_settings
                    WHERE scope = %s AND namespace = %s
                    """,
                    (scope.value, namespace),
                )
                row = cursor.fetchone()
                if not row:
                    return None
                settings, updated_at = row
                return SettingsRecord(
                    scope=scope,
                    namespace=namespace,
                    settings=settings,
                    updated_at=updated_at.isoformat() if updated_at else None,
                )

    def put(
        self,
        scope: SettingsScope,
        namespace: str,
        settings: dict[str, Any],
        schema: dict[str, Any] | None = None,
    ) -> SettingsRecord:
        self._validate(settings, schema)
        with psycopg2.connect(self._db_url) as conn:
            self._ensure_table(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO phlo_settings (scope, namespace, settings, updated_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (scope, namespace)
                    DO UPDATE SET settings = EXCLUDED.settings, updated_at = NOW()
                    RETURNING settings, updated_at
                    """,
                    (scope.value, namespace, settings),
                )
                stored_settings, updated_at = cursor.fetchone()
                conn.commit()
                return SettingsRecord(
                    scope=scope,
                    namespace=namespace,
                    settings=stored_settings,
                    updated_at=updated_at.isoformat() if updated_at else None,
                )

    def _validate(self, settings: dict[str, Any], schema: dict[str, Any] | None) -> None:
        if not schema:
            return
        try:
            validate(instance=settings, schema=schema)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc

    def _ensure_table(self, conn) -> None:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS phlo_settings (
                    scope TEXT NOT NULL,
                    namespace TEXT NOT NULL,
                    settings JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (scope, namespace)
                )
                """
            )
            conn.commit()


@lru_cache(maxsize=1)
def get_settings_service() -> SettingsService:
    settings = get_settings()
    db_url = settings.observatory_settings_db_url or settings.get_postgres_connection_string()
    return SettingsService(db_url)
