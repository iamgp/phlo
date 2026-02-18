"""Postgres-backed settings store."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from typing import Any

import psycopg2
from jsonschema import ValidationError, validate

from phlo.logging import get_logger
from phlo_observatory.settings import get_settings as get_observatory_settings

logger = get_logger(__name__)


class SettingsScope(StrEnum):
    """Supported settings scopes."""

    GLOBAL = "global"
    EXTENSION = "extension"


@dataclass(frozen=True)
class SettingsRecord:
    """Stored settings payload and metadata."""

    scope: SettingsScope
    namespace: str
    settings: dict[str, Any]
    updated_at: str | None


class SettingsService:
    """Settings service with optional schema validation."""

    def __init__(self, db_url: str) -> None:
        """Initialize settings persistence with a Postgres connection URL."""
        self._db_url = db_url
        self._table_ensured = False

    def get(self, scope: SettingsScope, namespace: str) -> SettingsRecord | None:
        """Get settings for a scope and namespace.

        Args:
            scope: Settings scope.
            namespace: Scope-specific settings namespace.

        Returns:
            Stored settings record, or ``None`` when not found.
        """
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
                    logger.debug(
                        "observatory_settings_not_found",
                        scope=scope.value,
                        namespace=namespace,
                    )
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
        """Upsert settings for a scope and namespace.

        Args:
            scope: Settings scope.
            namespace: Scope-specific settings namespace.
            settings: Settings payload to persist.
            schema: Optional JSON schema used to validate ``settings``.

        Returns:
            Persisted settings record.
        """
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
            logger.warning("observatory_settings_validation_failed", error=str(exc))
            raise ValueError(str(exc)) from exc

    def _ensure_table(self, conn) -> None:
        if self._table_ensured:
            return
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
        self._table_ensured = True
        logger.debug("observatory_settings_table_ensured")


class InMemorySettingsService:
    """In-memory fallback settings service for non-Postgres environments."""

    def __init__(self) -> None:
        self._store: dict[tuple[SettingsScope, str], SettingsRecord] = {}

    def get(self, scope: SettingsScope, namespace: str) -> SettingsRecord | None:
        return self._store.get((scope, namespace))

    def put(
        self,
        scope: SettingsScope,
        namespace: str,
        settings: dict[str, Any],
        schema: dict[str, Any] | None = None,
    ) -> SettingsRecord:
        if schema:
            try:
                validate(instance=settings, schema=schema)
            except ValidationError as exc:
                raise ValueError(str(exc)) from exc
        record = SettingsRecord(scope=scope, namespace=namespace, settings=settings, updated_at=None)
        self._store[(scope, namespace)] = record
        return record


@lru_cache(maxsize=1)
def get_settings_service() -> SettingsService | InMemorySettingsService:
    """Build and cache the settings service instance.

    Falls back to in-memory storage when Postgres integration is unavailable.
    """
    observatory_settings = get_observatory_settings()
    if observatory_settings.observatory_settings_db_url:
        logger.debug("observatory_settings_service_initialized", backend="postgres_explicit")
        return SettingsService(observatory_settings.observatory_settings_db_url)

    try:
        from phlo_postgres.settings import get_settings as get_postgres_settings
    except Exception:
        logger.warning("observatory_settings_falling_back_to_memory")
        return InMemorySettingsService()

    postgres_settings = get_postgres_settings()
    db_url = postgres_settings.get_postgres_connection_string()
    logger.debug("observatory_settings_service_initialized", backend="postgres_default")
    return SettingsService(db_url)
