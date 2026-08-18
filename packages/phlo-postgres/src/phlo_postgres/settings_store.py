"""PostgreSQL settings store capability for Observatory settings.

Registers a durable ``SettingsStoreSpec`` with the phlo capability registry
so that core's ``get_settings_service`` can resolve it without importing
this package directly.
"""

from __future__ import annotations

from phlo.capabilities import SettingsStoreSpec
from phlo.plugins.observatory_settings import SettingsService
from phlo_postgres.settings import get_settings as get_postgres_settings


class PostgresSettingsStore(SettingsService):
    """Durable Observatory settings store backed by PostgreSQL.

    The DSN is resolved from :mod:`phlo_postgres.settings` at construction
    time (config-only, no connection).  Actual database connections happen
    per-request inside ``get``/``put``, so a transient outage does not
    poison the instance — the next call retries the connection.
    """

    def __init__(self) -> None:
        postgres_settings = get_postgres_settings()
        super().__init__(postgres_settings.get_postgres_connection_string())


def get_settings_stores() -> list[SettingsStoreSpec]:
    """Return capability specs for the PostgreSQL settings store."""
    return [
        SettingsStoreSpec(
            name="postgres",
            provider=PostgresSettingsStore(),
        )
    ]
