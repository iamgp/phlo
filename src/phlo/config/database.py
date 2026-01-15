from pydantic import AliasChoices, Field

from phlo.config.base import BaseConfig


class DatabaseConfig(BaseConfig):
    """PostgreSQL database connection and schema configuration."""

    postgres_host: str = Field(default="postgres", description="PostgreSQL host")
    postgres_port: int = Field(default=10000, description="PostgreSQL port")
    postgres_user: str = Field(default="lake", description="PostgreSQL username")
    postgres_password: str = Field(default="phlo", description="PostgreSQL password")
    postgres_db: str = Field(default="lakehouse", description="PostgreSQL database name")
    postgres_mart_schema: str = Field(
        default="marts", description="Schema for published mart tables"
    )
    lineage_db_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PHLO_LINEAGE_DB_URL", "DAGSTER_PG_DB_CONNECTION_STRING"),
        description="PostgreSQL DSN for the row-level lineage store",
    )
    observatory_settings_db_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PHLO_OBSERVATORY_SETTINGS_DB_URL"),
        description="PostgreSQL DSN for Observatory settings storage",
    )

    def get_postgres_connection_string(self, include_db: bool = True) -> str:
        """
        Construct PostgreSQL connection string.

        Args:
            include_db: If True, include database name in connection string

        Returns:
            PostgreSQL connection string
        """
        db_part = f"/{self.postgres_db}" if include_db else ""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}{db_part}"
        )
