"""Core settings storage contracts and helpers for Observatory backends.

Core defines a neutral ``SettingsStore`` capability contract.  The durable
PostgreSQL implementation is registered by ``phlo-postgres`` through the
capability registry; core never imports a provider package.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal, Protocol, runtime_checkable

from jsonschema import ValidationError, validate
from pydantic import AliasChoices, Field

from phlo.config.base import BaseConfig
from phlo.logging import get_logger

logger = get_logger(__name__)


class StorageUnavailableError(RuntimeError):
    """Sanitised error raised when durable settings storage is unavailable.

    The API boundary maps this to HTTP 503.  The message never contains
    a DSN, password, or other credential.
    """


def _get_psycopg2():
    try:
        import psycopg2
        import psycopg2.extras
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "psycopg2 is required to use PostgreSQL-backed observatory settings storage."
        ) from exc
    return psycopg2


class ObservatorySettingsStorageConfig(BaseConfig):
    """Configuration for Observatory settings storage.

    The default backend is ``postgres`` (durable).  ``memory`` is permitted
    only through explicit development/test configuration and is rejected
    during regulated startup validation.
    """

    observatory_settings_backend: Literal["postgres", "memory"] = Field(
        default="postgres",
        validation_alias=AliasChoices("PHLO_OBSERVATORY_SETTINGS_BACKEND"),
        description="Settings storage backend: 'postgres' (durable, default) or 'memory' (dev/test only)",
    )

    observatory_settings_db_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PHLO_OBSERVATORY_SETTINGS_DB_URL"),
        description="PostgreSQL DSN override for Observatory settings storage",
    )


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


@runtime_checkable
class SettingsStore(Protocol):
    """Neutral capability contract for durable settings storage.

    Both global and extension settings endpoints resolve the same
    ``settings_store`` capability; there is no separate per-scope backend.
    """

    def get(self, scope: SettingsScope, namespace: str) -> SettingsRecord | None: ...

    def put(
        self,
        scope: SettingsScope,
        namespace: str,
        settings: dict[str, Any],
        schema: dict[str, Any] | None = None,
    ) -> SettingsRecord: ...


class SettingsService:
    """PostgreSQL-backed settings store with optional schema validation.

    This class lives in core so that existing re-exports remain stable, but
    it is never coupled to a provider package.  The durable instance used
    at runtime is registered by ``phlo-postgres`` through the capability
    registry and resolved by :func:`get_settings_service`.
    """

    def __init__(self, db_url: str) -> None:
        self._db_url = db_url
        self._table_ensured = False

    def get(self, scope: SettingsScope, namespace: str) -> SettingsRecord | None:
        """Get settings for a scope and namespace."""
        psycopg2 = _get_psycopg2()
        try:
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
        except Exception as exc:
            if isinstance(exc, StorageUnavailableError):
                raise
            logger.warning("observatory_settings_storage_unavailable", scope=scope.value)
            raise StorageUnavailableError("Settings storage is unavailable") from exc

    def put(
        self,
        scope: SettingsScope,
        namespace: str,
        settings: dict[str, Any],
        schema: dict[str, Any] | None = None,
    ) -> SettingsRecord:
        """Upsert settings for a scope and namespace."""
        self._validate(settings, schema)
        psycopg2 = _get_psycopg2()
        json_settings = psycopg2.extras.Json(settings)
        try:
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
                        (scope.value, namespace, json_settings),
                    )
                    stored_settings, updated_at = cursor.fetchone()
                    conn.commit()
                    return SettingsRecord(
                        scope=scope,
                        namespace=namespace,
                        settings=stored_settings,
                        updated_at=updated_at.isoformat() if updated_at else None,
                    )
        except Exception as exc:
            if isinstance(exc, (StorageUnavailableError, ValueError)):
                raise
            logger.warning("observatory_settings_storage_unavailable", scope=scope.value)
            raise StorageUnavailableError("Settings storage is unavailable") from exc

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
    """In-memory settings service for explicit development/test configuration.

    This backend is never selected by default.  It is returned only when
    ``observatory_settings_backend`` is explicitly set to ``memory`` and
    is rejected during regulated startup validation.
    """

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
        record = SettingsRecord(
            scope=scope,
            namespace=namespace,
            settings=settings,
            updated_at=None,
        )
        self._store[(scope, namespace)] = record
        return record


# Module-level singleton for memory mode so that writes persist across
# requests within a single dev/test process.  Durable (postgres) mode
# does NOT use this cache — it resolves the capability on every call.
_memory_service: InMemorySettingsService | None = None


def get_settings_service() -> SettingsStore:
    """Resolve the settings store for the configured backend.

    - ``postgres`` (default): resolves the ``settings_store`` capability
      registered by ``phlo-postgres``.  If the capability is not registered
      or the connection fails, :class:`StorageUnavailableError` is raised
      so the API boundary can return 503.  A later call retries capability
      resolution and recovers without a process restart.

    - ``memory`` (explicit dev/test): returns a process-local
      :class:`InMemorySettingsService` singleton.  Rejected in regulated mode.

    An explicit ``observatory_settings_db_url`` overrides the capability
      and creates a :class:`SettingsService` directly.

    This function is NOT cached: each call performs a fresh capability
      resolution so that transient failures are never sticky.
    """
    config = ObservatorySettingsStorageConfig()
    backend = config.observatory_settings_backend

    if backend == "memory":
        global _memory_service
        if _memory_service is None:
            _memory_service = InMemorySettingsService()
            logger.debug("observatory_settings_service_initialized", backend="memory")
        return _memory_service

    # postgres mode (default) — explicit DSN override takes precedence
    if config.observatory_settings_db_url:
        logger.debug("observatory_settings_service_initialized", backend="postgres_explicit")
        return SettingsService(config.observatory_settings_db_url)

    # Resolve the durable settings store through the neutral capability
    # registry.  Core never imports a provider package directly.
    from phlo.capabilities import resolve_capability

    result = resolve_capability("settings_store")
    if result is None:
        logger.warning("observatory_settings_storage_unavailable", reason="no_provider")
        raise StorageUnavailableError(
            "Durable settings storage backend is not available"
        )
    logger.debug(
        "observatory_settings_service_initialized",
        backend="postgres_capability",
        provider=result.name,
    )
    return result.provider


def _reset_memory_service() -> None:
    """Clear the memory-mode singleton (test helper)."""
    global _memory_service
    _memory_service = None
