"""Publish target wrapper for Postgres serving outputs."""

from __future__ import annotations

from dataclasses import dataclass, field

from phlo_postgres.resource import PostgresResource
from phlo_postgres.settings import get_settings


@dataclass
class PostgresPublishTarget:
    """Structured publish target for Postgres serving tables."""

    resource: PostgresResource = field(default_factory=PostgresResource)
    target_system: str = "postgres"

    @property
    def default_schema(self) -> str:
        """Return the default serving schema for published mart tables."""
        return get_settings().postgres_mart_schema
