from __future__ import annotations

import duckdb
from dagster import ConfigurableResource

from cascade.ducklake import (
    build_ducklake_runtime_config,
    configure_ducklake_connection,
)


class DuckLakeResource(ConfigurableResource):
    """Dagster resource providing a configured DuckLake connection."""

    read_only: bool = False

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """
        Return a DuckDB connection attached to DuckLake.

        The connection installs required extensions, configures DuckLake retries,
        and ensures raw/curated schemas exist.
        
        Uses ephemeral :memory: connection for concurrency safety.
        """
        conn = duckdb.connect(database=":memory:")
        runtime = build_ducklake_runtime_config()
        configure_ducklake_connection(
            conn,
            runtime=runtime,
            ensure_schemas={"raw", "main_raw", "main_staging", "main_curated"},
            read_only=self.read_only,
        )
        return conn
