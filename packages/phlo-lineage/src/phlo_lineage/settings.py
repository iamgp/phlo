"""Lineage settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field

from phlo.config.base import BaseConfig


class LineageSettings(BaseConfig):
    """Lineage store configuration."""

    lineage_db_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "LINEAGE_DB_URL",
            "PHLO_LINEAGE_DB_URL",
            "DAGSTER_PG_DB_CONNECTION_STRING",
        ),
        description="PostgreSQL DSN for the row-level lineage store",
    )


@lru_cache(maxsize=1)
def get_settings() -> LineageSettings:
    return LineageSettings()
