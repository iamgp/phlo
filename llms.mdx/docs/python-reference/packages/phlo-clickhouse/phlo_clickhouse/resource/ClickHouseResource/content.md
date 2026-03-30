# ClickHouseResource (/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/resource/ClickHouseResource)



Resource wrapper for ClickHouse connections and query execution.

Manages ClickHouse database connections and provides methods for
executing queries, managing tables, and ingesting data.

Attributes [#attributes]

<PyAttribute name="&#x22;host&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  ClickHouse server hostname. Uses settings default if None.
</PyAttribute>

<PyAttribute name="&#x22;port&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;">
  ClickHouse HTTP port. Uses settings default if None.
</PyAttribute>

<PyAttribute name="&#x22;user&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  ClickHouse username. Uses settings default if None.
</PyAttribute>

<PyAttribute name="&#x22;password&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  ClickHouse password. Uses settings default if None.
</PyAttribute>

<PyAttribute name="&#x22;database&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Default database name. Uses settings default if None.
</PyAttribute>

<PyAttribute name="&#x22;secure&#x22;" type="&#x22;bool | None&#x22;" value="&#x22;None&#x22;">
  Whether to use TLS/SSL connection. Uses settings default if None.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;_settings&#x22;" type="&#x22;(self)&#x22;">
  Return ClickHouse settings from configuration.

  <PySourceCode>
    ```python
    def _settings(self):
        """Return ClickHouse settings from configuration.

        Returns:
            ClickHouseSettings instance with configured defaults.

        """
        return get_clickhouse_settings()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="null">
    ClickHouseSettings instance with configured defaults.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_client&#x22;" type="&#x22;(self) -> 'Client'&#x22;">
  Create and return a ClickHouse database client.

  Establishes a connection to ClickHouse using configured or default
  connection parameters.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > resource = ClickHouseResource()
    > > > client = resource.get\_client()
    > > > result = client.query("SELECT 1")
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;'Client'&#x22;">
    ClickHouse client instance ready for query execution.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, sql, params=None) -> list[list[Any]]&#x22;">
  Execute a SQL query and return results.

  Runs a SELECT query against ClickHouse and returns the result rows.
  The client connection is automatically closed after execution.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > resource = ClickHouseResource()
    > > > rows = resource.execute("SELECT number FROM system.numbers LIMIT 3")
    > > > len(rows)
    > > > 3
  </Callout>

  <PySourceCode>
    ```python
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
            return result.result_rows
        finally:
            client.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;sql&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL query string to execute.
    </PyParameter>

    <PyParameter name="&#x22;params&#x22;" type="&#x22;Iterable[object] | None&#x22;" value="&#x22;None&#x22;">
      Optional iterable of query parameters for substitution.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of result rows, where each row is a list of column values.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;command&#x22;" type="&#x22;(self, sql) -> Any&#x22;">
  Execute a command (DDL/DML) that returns a single value or None.

  Executes statements like CREATE TABLE, INSERT, ALTER, etc.
  The client connection is automatically closed after execution.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > resource = ClickHouseResource()
    > > > result = resource.command("CREATE TABLE test (id Int32) ENGINE = Memory")
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;sql&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL command string to execute.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Single value result for commands that return data, or None.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;wait_ready&#x22;" type="&#x22;(self, *, timeout=60.0, interval=1.0) -> None&#x22;">
  Wait for ClickHouse server to become ready for queries.

  Polls the ClickHouse server with a simple health check query until
  it responds successfully or the timeout is reached.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > resource = ClickHouseResource()
    > > > resource.wait\_ready(timeout=30.0)  # Blocks until ready
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;float&#x22;" value="&#x22;60.0&#x22;">
      Maximum time to wait in seconds. Defaults to 60.0.
    </PyParameter>

    <PyParameter name="&#x22;interval&#x22;" type="&#x22;float&#x22;" value="&#x22;1.0&#x22;">
      Time between retry attempts in seconds. Defaults to 1.0.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_escape_identifier&#x22;" type="&#x22;(self, name) -> str&#x22;">
  Escape a ClickHouse identifier with backticks.

  Escapes database names, table names, or column names for safe use
  in SQL queries. Handles existing backticks by doubling them.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > resource = ClickHouseResource()
    > > > resource.\_escape\_identifier("my-table")
    > > > '`my-table`'
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Identifier string to escape.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Escaped identifier wrapped in backticks.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;ensure_table&#x22;" type="&#x22;(self, *, table_name, schema, partition_spec=None, override_ref=None) -> Any&#x22;">
  Ensure a destination table exists, creating it if necessary.

  Creates a ClickHouse table with the specified schema if it doesn't
  already exist. Supports optional partitioning.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > from pandera import Schema, Column, Int64
    > > > class MySchema(Schema):
    > > > ...     id = Column(Int64)
    > > > resource = ClickHouseResource()
    > > > resource.ensure\_table(table\_name="my\_table", schema=MySchema)
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of the table to create.
    </PyParameter>

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Schema definition (Pandera schema or similar).
    </PyParameter>

    <PyParameter name="&#x22;partition_spec&#x22;" type="&#x22;Any&#x22;" value="&#x22;None&#x22;">
      Optional list of (column\_name, type) tuples for partitioning.
    </PyParameter>

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional reference override (not implemented).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Result of the CREATE TABLE command.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;append_parquet&#x22;" type="&#x22;(self, *, table_name, data_path, override_ref=None) -> dict[str, int]&#x22;">
  Append Parquet file data to a ClickHouse table.

  Reads a Parquet file and inserts all rows into the specified table.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > resource = ClickHouseResource()
    > > > result = resource.append\_parquet(
    > > > ...     table\_name="events",
    > > > ...     data\_path="/data/events.parquet"
    > > > ... )
    > > > result\["rows\_inserted"]
    > > > 1000
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Target table name for data insertion.
    </PyParameter>

    <PyParameter name="&#x22;data_path&#x22;" type="&#x22;str | Path&#x22;" value="undefined">
      Path to the Parquet file to load.
    </PyParameter>

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional reference override (not implemented).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary with "rows\_inserted" count.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;merge_parquet&#x22;" type="&#x22;(self, *, table_name, data_path, unique_key, override_ref=None) -> dict[str, int]&#x22;">
  Merge Parquet file data into a ClickHouse table using upsert logic.

  Implements a merge/upsert operation: deletes existing rows with matching
  unique keys, then inserts new data from the Parquet file.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > resource = ClickHouseResource()
    > > > result = resource.merge\_parquet(
    > > > ...     table\_name="events",
    > > > ...     data\_path="/data/events.parquet",
    > > > ...     unique\_key="event\_id"
    > > > ... )
    > > > result\["rows\_inserted"], result\["rows\_deleted"]
    > > > (100, 100)
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Target table name for data merge.
    </PyParameter>

    <PyParameter name="&#x22;data_path&#x22;" type="&#x22;str | Path&#x22;" value="undefined">
      Path to the Parquet file containing new data.
    </PyParameter>

    <PyParameter name="&#x22;unique_key&#x22;" type="&#x22;str&#x22;" value="undefined">
      Column name to use as the unique identifier for matching.
    </PyParameter>

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional reference override (not implemented).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary with "rows\_inserted" and "rows\_deleted" counts.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_schema_to_columns&#x22;" type="&#x22;(self, schema) -> str&#x22;">
  Convert a schema definition to ClickHouse column definitions.

  Supports Pandera schemas (with 'columns' attribute) or dataclass-like
  schemas (with 'fields' attribute).

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > from pandera import Schema, Column, Int64, String
    > > > class TestSchema(Schema):
    > > > ...     id = Column(Int64)
    > > > ...     name = Column(String)
    > > > resource = ClickHouseResource()
    > > > resource.\_schema\_to\_columns(TestSchema)
    > > > 'id Int64, name String'
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Schema object with either 'columns' or 'fields' attribute.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Comma-separated string of "name type" column definitions.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_pandas_type_to_clickhouse&#x22;" type="&#x22;(self, dtype) -> str&#x22;">
  Convert a pandas dtype to ClickHouse type string.

  Maps common pandas data types to their ClickHouse equivalents.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > import pandas as pd
    > > > resource = ClickHouseResource()
    > > > resource.\_pandas\_type\_to\_clickhouse(pd.Int64Dtype())
    > > > 'Int64'
    > > > resource.\_pandas\_type\_to\_clickhouse(pd.StringDtype())
    > > > 'String'
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;dtype&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Pandas dtype object to convert.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    ClickHouse type name as a string.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_python_type_to_clickhouse&#x22;" type="&#x22;(self, py_type) -> str&#x22;">
  Convert a Python type to ClickHouse type string.

  Maps Python built-in types to their ClickHouse equivalents.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > resource = ClickHouseResource()
    > > > resource.\_python\_type\_to\_clickhouse(int)
    > > > 'Int64'
    > > > resource.\_python\_type\_to\_clickhouse(str)
    > > > 'String'
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;py_type&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Python type to convert.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    ClickHouse type name as a string. Defaults to "String" for unknown types.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, host=None, port=None, user=None, password=None, database=None, secure=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;host&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;port&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;user&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;password&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;database&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;secure&#x22;" type="&#x22;bool | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
