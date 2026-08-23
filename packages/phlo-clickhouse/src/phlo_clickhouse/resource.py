"""ClickHouse resource for executing queries.

This module provides the ClickHouseResource class for managing ClickHouse
database connections, executing queries, and handling data operations
including table creation and Parquet file ingestion.

Example:
    Basic resource usage:

    >>> from phlo_clickhouse.resource import ClickHouseResource
    >>> resource = ClickHouseResource()
    >>> resource.execute("SELECT 1")
    [[1]]


Re-exported as ClickHouseResource from the phlo_clickhouse package root; builds
on the capability contracts in phlo.capabilities.
"""

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
    """Resource wrapper for ClickHouse connections and query execution.

    Manages ClickHouse database connections and provides methods for
    executing queries, managing tables, and ingesting data.

    Attributes:
        host: ClickHouse server hostname. Uses settings default if None.
        port: ClickHouse HTTP port. Uses settings default if None.
        user: ClickHouse username. Uses settings default if None.
        password: ClickHouse password. Uses settings default if None.
        database: Default database name. Uses settings default if None.
        secure: Whether to use TLS/SSL connection. Uses settings default if None.

    Example:
        >>> resource = ClickHouseResource(host="localhost", database="test")
        >>> client = resource.get_client()

    """

    host: str | None = None
    port: int | None = None
    user: str | None = None
    password: str | None = None
    database: str | None = None
    secure: bool | None = None

    def _settings(self):
        """Return ClickHouse settings from configuration.

        Returns:
            ClickHouseSettings instance with configured defaults.

        """
        return get_clickhouse_settings()

    def get_client(self) -> "Client":
        """Create and return a ClickHouse database client.

        Establishes a connection to ClickHouse using configured or default
        connection parameters.

        Returns:
            ClickHouse client instance ready for query execution.

        Example:
            >>> resource = ClickHouseResource()
            >>> client = resource.get_client()
            >>> result = client.query("SELECT 1")

        """
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
        """Execute a SQL query and return results.

        Runs a SELECT query against ClickHouse and returns the result rows.
        The client connection is automatically closed after execution.

        Args:
            sql: SQL query string to execute.
            params: Optional iterable of query parameters for substitution.

        Returns:
            List of result rows, where each row is a list of column values.

        Example:
            >>> resource = ClickHouseResource()
            >>> rows = resource.execute("SELECT number FROM system.numbers LIMIT 3")
            >>> len(rows)
            3

        """
        client = self.get_client()
        try:
            result = client.query(sql, parameters=list(params or []))
            return [list(row) for row in result.result_rows]
        finally:
            client.close()

    def command(self, sql: str) -> Any:
        """Execute a command (DDL/DML) that returns a single value or None.

        Executes statements like CREATE TABLE, INSERT, ALTER, etc.
        The client connection is automatically closed after execution.

        Args:
            sql: SQL command string to execute.

        Returns:
            Single value result for commands that return data, or None.

        Example:
            >>> resource = ClickHouseResource()
            >>> result = resource.command("CREATE TABLE test (id Int32) ENGINE = Memory")

        """
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
        """Wait for ClickHouse server to become ready for queries.

        Polls the ClickHouse server with a simple health check query until
        it responds successfully or the timeout is reached.

        Args:
            timeout: Maximum time to wait in seconds. Defaults to 60.0.
            interval: Time between retry attempts in seconds. Defaults to 1.0.

        Raises:
            TimeoutError: If ClickHouse is not ready within the timeout period.

        Example:
            >>> resource = ClickHouseResource()
            >>> resource.wait_ready(timeout=30.0)  # Blocks until ready

        """
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
        """Escape a ClickHouse identifier with backticks.

        Escapes database names, table names, or column names for safe use
        in SQL queries. Handles existing backticks by doubling them.

        Args:
            name: Identifier string to escape.

        Returns:
            Escaped identifier wrapped in backticks.

        Example:
            >>> resource = ClickHouseResource()
            >>> resource._escape_identifier("my-table")
            '`my-table`'

        """
        return f"`{name.replace('`', '``')}`"

    def ensure_table(
        self,
        *,
        table_name: str,
        schema: Any,
        partition_spec: Any = None,
        override_ref: str | None = None,
    ) -> Any:
        """Ensure a destination table exists, creating it if necessary.

        Creates a ClickHouse table with the specified schema if it doesn't
        already exist. Supports optional partitioning.

        Args:
            table_name: Name of the table to create.
            schema: Schema definition (Pandera schema or similar).
            partition_spec: Optional list of (column_name, type) tuples for partitioning.
            override_ref: Optional reference override (not implemented).

        Returns:
            Result of the CREATE TABLE command.

        Example:
            >>> from pandera import Schema, Column, Int64
            >>> class MySchema(Schema):
            ...     id = Column(Int64)
            >>> resource = ClickHouseResource()
            >>> resource.ensure_table(table_name="my_table", schema=MySchema)

        """
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
        """Append Parquet file data to a ClickHouse table.

        Reads a Parquet file and inserts all rows into the specified table.

        Args:
            table_name: Target table name for data insertion.
            data_path: Path to the Parquet file to load.
            override_ref: Optional reference override (not implemented).

        Returns:
            Dictionary with "rows_inserted" count.

        Example:
            >>> resource = ClickHouseResource()
            >>> result = resource.append_parquet(
            ...     table_name="events",
            ...     data_path="/data/events.parquet"
            ... )
            >>> result["rows_inserted"]
            1000

        """
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
        """Merge Parquet file data into a ClickHouse table using upsert logic.

        Implements a merge/upsert operation: deletes existing rows with matching
        unique keys, then inserts new data from the Parquet file.

        Args:
            table_name: Target table name for data merge.
            data_path: Path to the Parquet file containing new data.
            unique_key: Column name to use as the unique identifier for matching.
            override_ref: Optional reference override (not implemented).

        Returns:
            Dictionary with "rows_inserted" and "rows_deleted" counts.

        Example:
            >>> resource = ClickHouseResource()
            >>> result = resource.merge_parquet(
            ...     table_name="events",
            ...     data_path="/data/events.parquet",
            ...     unique_key="event_id"
            ... )
            >>> result["rows_inserted"], result["rows_deleted"]
            (100, 100)

        """
        settings = self._settings()
        database = self._escape_identifier(self.database or settings.clickhouse_db)
        table = self._escape_identifier(table_name)
        key = self._escape_identifier(unique_key)

        data_path_str = str(data_path)
        df = pd.read_parquet(data_path_str)
        row_count = len(df)

        unique_keys = df[unique_key].tolist()
        # ALTER TABLE ... DELETE is a background mutation and returns before
        # affected rows are actually removed (mutations_sync is left unset).
        # The insert below therefore races the delete: readers may transiently
        # observe both the old and the new version of a key.
        if unique_keys:
            keys_str = ", ".join(f"'{k}'" for k in unique_keys)
            delete_sql = f"ALTER TABLE {database}.{table} DELETE WHERE {key} IN ({keys_str})"
            self.command(delete_sql)

        client = self.get_client()
        try:
            client.insert_df(f"{database}.{table}", df)
        finally:
            client.close()

        return {"rows_inserted": row_count, "rows_deleted": len(unique_keys)}

    def _schema_to_columns(self, schema: Any) -> str:
        """Convert a schema definition to ClickHouse column definitions.

        Supports Pandera schemas (with 'columns' attribute) or dataclass-like
        schemas (with 'fields' attribute).

        Args:
            schema: Schema object with either 'columns' or 'fields' attribute.

        Returns:
            Comma-separated string of "name type" column definitions.

        Raises:
            TypeError: If the schema type is not supported.

        Example:
            >>> from pandera import Schema, Column, Int64, String
            >>> class TestSchema(Schema):
            ...     id = Column(Int64)
            ...     name = Column(String)
            >>> resource = ClickHouseResource()
            >>> resource._schema_to_columns(TestSchema)
            'id Int64, name String'

        """
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
        """Convert a pandas dtype to ClickHouse type string.

        Maps common pandas data types to their ClickHouse equivalents.

        Args:
            dtype: Pandas dtype object to convert.

        Returns:
            ClickHouse type name as a string.

        Example:
            >>> import pandas as pd
            >>> resource = ClickHouseResource()
            >>> resource._pandas_type_to_clickhouse(pd.Int64Dtype())
            'Int64'
            >>> resource._pandas_type_to_clickhouse(pd.StringDtype())
            'String'

        """
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
        """Convert a Python type to ClickHouse type string.

        Maps Python built-in types to their ClickHouse equivalents.

        Args:
            py_type: Python type to convert.

        Returns:
            ClickHouse type name as a string. Defaults to "String" for unknown types.

        Example:
            >>> resource = ClickHouseResource()
            >>> resource._python_type_to_clickhouse(int)
            'Int64'
            >>> resource._python_type_to_clickhouse(str)
            'String'

        """
        type_map = {
            int: "Int64",
            float: "Float64",
            str: "String",
            bool: "UInt8",
        }
        return type_map.get(py_type, "String")
