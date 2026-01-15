from pydantic import Field

from phlo.config.base import BaseConfig


class QueryConfig(BaseConfig):
    """Trino distributed SQL query engine configuration."""

    trino_version: str = Field(default="477", description="Trino version")
    trino_port: int = Field(default=10005, description="Trino HTTP port")
    trino_host: str = Field(default="trino", description="Trino service hostname")
    trino_catalog: str = Field(default="iceberg", description="Trino catalog name for Iceberg")

    @property
    def trino_connection_string(self) -> str:
        """Return Trino connection string for SQLAlchemy/dbt."""
        return f"trino://{self.trino_host}:{self.trino_port}/{self.trino_catalog}"
