"""Postgres settings."""

from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field

from phlo.config.base import BaseConfig


class PostgresSettings(BaseConfig):
    """PostgreSQL database connection and schema configuration."""

    postgres_host: str = Field(default="postgres", description="PostgreSQL host")
    postgres_port: int = Field(default=10000, description="PostgreSQL port")
    postgres_user: str = Field(default="lake", description="PostgreSQL username")
    postgres_password: str = Field(default="phlo", description="PostgreSQL password")
    postgres_db: str = Field(default="lakehouse", description="PostgreSQL database name")
    postgres_mart_schema: str = Field(
        default="marts", description="Schema for published mart tables"
    )

    def get_postgres_connection_string(self, include_db: bool = True) -> str:
        db_part = f"/{self.postgres_db}" if include_db else ""
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        return f"postgresql://{user}:{password}@{self.postgres_host}:{self.postgres_port}{db_part}"


@lru_cache(maxsize=1)
def get_settings() -> PostgresSettings:
    return PostgresSettings()
