"""ClickHouse resource for executing queries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import TYPE_CHECKING, Any, Iterable

import clickhouse_connect
import pandas as pd

from phlo.capabilities import CapabilitySupport
from phlo.logging import get_logger
from phlo_clickhouse.settings import get_settings as get_clickhouse_settings

if TYPE_CHECKING:
    from clickhouse_connect.driver import Client

logger = get_logger(__name__)

CLICKHOUSE_QUERY_ENGINE_SUPPORT = CapabilitySupport(
    supports_snapshots=False,
    supports_time_travel=False,
)


@dataclass
class ClickHouseResource:
    """Resource wrapper for ClickHouse connections and query execution."""

    host: str | None = None
    port: int | None = None
    user: str | None = None
    password: str | None = None
    database: str | None = None
    secure: bool | None = None

    def _settings(self):
        return get_clickhouse_settings()

    def get_client(self) -> "Client":
        """Create and return a ClickHouse client."""
        settings = self._settings()
        return clickhouse_connect.get_client(
            host=self.host or settings.clickhouse_host,
            port=self.port or settings.clickhouse_http_port,
            username=self.user or settings.clickhouse_user,
            password=self.password or settings.clickhouse_password,
            database=self.database or settings.clickhouse_db,
            secure=self.secure if self.secure is not None else settings.clickhouse_secure,
        )

    def execute(self, sql: str, params: Iterable[object] | None = None) -> list[list[Any]]:
        """Execute SQL and return query results."""
        client = self.get_client()
        try:
            result = client.query(sql, parameters=list(params or []))
            return result.result_rows
        finally:
            client.close()

    def command(self, sql: str) -> Any:
        """Execute a command (DDL/DML) that returns a single value or None."""
        client = self.get_client()
        try:
            return client.command(sql)
        finally:
            client.close()

    def wait_ready(
        self,
        *,
        timeout: float = 60.0,
        interval: float = 1.0,
    ) -> None:
        """Wait for ClickHouse to accept queries."""
        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        interval = max(interval, 0.0)
        settings = self._settings()
        while time.monotonic() < deadline:
            try:
                self.command("SELECT 1")
                logger.info(
                    "clickhouse_wait_ready_succeeded",
                    host=self.host or settings.clickhouse_host,
                    port=self.port or settings.clickhouse_http_port,
                )
                return
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.debug(
                    "clickhouse_wait_ready_retry",
                    host=self.host or settings.clickhouse_host,
                    port=self.port or settings.clickhouse_http_port,
                    retry_interval_seconds=interval,
                )
                time.sleep(interval)
        logger.error(
            "clickhouse_wait_ready_timeout",
            host=self.host or settings.clickhouse_host,
            port=self.port or settings.clickhouse_http_port,
            timeout_seconds=timeout,
        )
        raise TimeoutError(f"ClickHouse not ready after {timeout:.1f}s") from last_error

    def _escape_identifier(self, name: str) -> str:
        """Escape a ClickHouse identifier (database, table, column) with backticks."""
        return f"`{name.replace('`', '``')}`"

    def ensure_table(
        self,
        *,
        table_name: str,
        schema: Any,
        partition_spec: Any = None,
        override_ref: str | None = None,
    ) -> Any:
        """Ensure a destination table exists."""
        settings = self._settings()
        database = self._escape_identifier(self.database or settings.clickhouse_db)
        table = self._escape_identifier(table_name)

        columns_def = self._schema_to_columns(schema)

        partition_by = ""
        if partition_spec:
            partition_cols = [self._escape_identifier(p[0]) for p in partition_spec]
            partition_by = f"PARTITION BY ({', '.join(partition_cols)})"

        sql = f"CREATE TABLE IF NOT EXISTS {database}.{table} ({columns_def}) ENGINE = MergeTree() {partition_by} ORDER BY tuple()"

        return self.command(sql)

    def append_parquet(
        self,
        *,
        table_name: str,
        data_path: str | Path,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Append staged parquet data to a destination table."""
        settings = self._settings()
        database = self._escape_identifier(self.database or settings.clickhouse_db)
        table = self._escape_identifier(table_name)

        data_path_str = str(data_path)
        df = pd.read_parquet(data_path_str)
        row_count = len(df)

        client = self.get_client()
        try:
            client.insert_df(f"{database}.{table}", df)
        finally:
            client.close()

        return {"rows_inserted": row_count}

    def merge_parquet(
        self,
        *,
        table_name: str,
        data_path: str | Path,
        unique_key: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Merge staged parquet data into a destination table."""
        settings = self._settings()
        database = self._escape_identifier(self.database or settings.clickhouse_db)
        table = self._escape_identifier(table_name)
        key = self._escape_identifier(unique_key)

        data_path_str = str(data_path)
        df = pd.read_parquet(data_path_str)
        row_count = len(df)

        sql = f"""
        INSERT INTO {database}.{table}
        SELECT * FROM file('{data_path_str}', Parquet)
        WHERE {key} NOT IN (
            SELECT {key} FROM {database}.{table}
        )
        """

        self.command(sql)
        return {"rows_inserted": row_count, "rows_deleted": 0}

    def _schema_to_columns(self, schema: Any) -> str:
        """Convert a schema to ClickHouse column definitions."""
        if hasattr(schema, "to_schema"):
            schema = schema.to_schema()

        if hasattr(schema, "columns"):
            columns = []
            for name, col in schema.columns.items():
                ch_type = self._pandas_type_to_clickhouse(col.dtype)
                columns.append(f"{name} {ch_type}")
            return ", ".join(columns)

        if hasattr(schema, "fields"):
            columns = []
            for field in schema.fields:
                ch_type = self._python_type_to_clickhouse(field.type)
                columns.append(f"{field.name} {ch_type}")
            return ", ".join(columns)

        raise TypeError(
            f"Unsupported schema type: {type(schema).__name__}. Expected a schema with 'columns' or 'fields' attribute."
        )

    def _pandas_type_to_clickhouse(self, dtype: Any) -> str:
        """Convert pandas dtype to ClickHouse type."""
        import pandas as pd

        if pd.api.types.is_integer_dtype(dtype):
            return "Int64"
        if pd.api.types.is_float_dtype(dtype):
            return "Float64"
        if pd.api.types.is_bool_dtype(dtype):
            return "UInt8"
        if pd.api.types.is_datetime64_any_dtype(dtype):
            return "DateTime64"
        if pd.api.types.is_string_dtype(dtype):
            return "String"
        return "String"

    def _python_type_to_clickhouse(self, py_type: Any) -> str:
        """Convert Python type to ClickHouse type."""
        type_map = {
            int: "Int64",
            float: "Float64",
            str: "String",
            bool: "UInt8",
        }
        return type_map.get(py_type, "String")
