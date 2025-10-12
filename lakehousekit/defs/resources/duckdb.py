from __future__ import annotations

import duckdb
from dagster import ConfigurableResource

from lakehousekit.config import config


class DuckDBResource(ConfigurableResource):
    """DuckDB connection resource with connection pooling support."""

    database_path: str = config.duckdb_warehouse_path

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """
        Get a DuckDB connection to the warehouse database.

        Returns:
            DuckDB connection object
        """
        return duckdb.connect(database=self.database_path)
