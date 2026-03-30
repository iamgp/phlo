# MockIcebergTable (/docs/python-reference/packages/phlo-testing/phlo_testing/placeholders/MockIcebergTable)



Mock Iceberg table backed by DuckDB.

Implements a subset of PyIceberg table interface using DuckDB
as the storage backend for fast testing.

Attributes [#attributes]

<PyAttribute name="&#x22;name&#x22;" type="null" value="&#x22;name&#x22;">
  Table identifier (e.g., "raw\.users").
</PyAttribute>

<PyAttribute name="&#x22;schema&#x22;" type="null" value="&#x22;schema&#x22;">
  PyIceberg Schema object.
</PyAttribute>

<PyAttribute name="&#x22;conn&#x22;" type="null" value="&#x22;conn&#x22;">
  DuckDB connection for data storage.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, name, schema, conn)&#x22;">
  Initialize mock table.

  <PySourceCode>
    ```python
    def __init__(self, name: str, schema: Schema, conn: "duckdb.DuckDBPyConnection"):
        """Initialize mock table.

        Args:
            name: Table name (e.g., "raw.users").
            schema: PyIceberg Schema object defining columns.
            conn: DuckDB connection for data storage.

        """
        self.name = name
        self.schema = schema
        self.conn = conn
        self._create_duckdb_table()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name (e.g., "raw\.users").
    </PyParameter>

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Schema&#x22;" value="undefined">
      PyIceberg Schema object defining columns.
    </PyParameter>

    <PyParameter name="&#x22;conn&#x22;" type="&#x22;duckdb.DuckDBPyConnection&#x22;" value="undefined">
      DuckDB connection for data storage.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;_iceberg_type_to_duckdb&#x22;" type="&#x22;(self, iceberg_type) -> str&#x22;">
  Convert PyIceberg type to DuckDB type string.

  <PySourceCode>
    ```python
    def _iceberg_type_to_duckdb(self, iceberg_type: Any) -> str:
        """Convert PyIceberg type to DuckDB type string.

        Args:
            iceberg_type: PyIceberg type object.

        Returns:
            DuckDB type string (e.g., "VARCHAR", "INTEGER").

        """
        if isinstance(iceberg_type, StringType):
            return "VARCHAR"
        elif isinstance(iceberg_type, IntegerType):
            return "INTEGER"
        elif isinstance(iceberg_type, LongType):
            return "BIGINT"
        elif isinstance(iceberg_type, FloatType):
            return "FLOAT"
        elif isinstance(iceberg_type, DoubleType):
            return "DOUBLE"
        elif isinstance(iceberg_type, BooleanType):
            return "BOOLEAN"
        elif isinstance(iceberg_type, TimestamptzType):
            return "TIMESTAMP WITH TIME ZONE"
        elif isinstance(iceberg_type, DateType):
            return "DATE"
        elif isinstance(iceberg_type, BinaryType):
            return "BLOB"
        else:
            # Default to VARCHAR for unknown types
            return "VARCHAR"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;iceberg_type&#x22;" type="&#x22;Any&#x22;" value="undefined">
      PyIceberg type object.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    DuckDB type string (e.g., "VARCHAR", "INTEGER").
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_create_duckdb_table&#x22;" type="&#x22;(self) -> None&#x22;">
  Create DuckDB table from Iceberg schema.

  Creates a table in DuckDB matching the PyIceberg schema.

  <PySourceCode>
    ```python
    def _create_duckdb_table(self) -> None:
        """Create DuckDB table from Iceberg schema.

        Creates a table in DuckDB matching the PyIceberg schema.
        """
        # Build CREATE TABLE statement
        columns = []
        for field in self.schema.fields:
            duckdb_type = self._iceberg_type_to_duckdb(field.field_type)
            nullable = "NULL" if not field.required else "NOT NULL"
            columns.append(f'"{field.name}" {duckdb_type} {nullable}')

        create_sql = f"CREATE TABLE IF NOT EXISTS {self.name} ({', '.join(columns)})"
        self.conn.execute(create_sql)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;append&#x22;" type="&#x22;(self, data) -> None&#x22;">
  Append data to table.

  <PySourceCode>
    ```python
    def append(self, data: Union[pd.DataFrame, pa.Table]) -> None:
        """Append data to table.

        Args:
            data: Pandas DataFrame or PyArrow Table to append.

        Raises:
            ValueError: If data schema doesn't match table schema.

        """
        if isinstance(data, pa.Table):
            data = data.to_pandas()

        # Insert into DuckDB table (data is now a pandas DataFrame)
        self.conn.execute(f"INSERT INTO {self.name} SELECT * FROM data")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;data&#x22;" type="&#x22;Union[pd.DataFrame, pa.Table]&#x22;" value="undefined">
      Pandas DataFrame or PyArrow Table to append.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;scan&#x22;" type="&#x22;(self) -> MockTableScan&#x22;">
  Return a table scan for querying.

  <PySourceCode>
    ```python
    def scan(self) -> "MockTableScan":
        """Return a table scan for querying.

        Returns:
            MockTableScan instance for building queries.

        """
        return MockTableScan(self.name, self.conn)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.placeholders.MockTableScan&#x22;">
    MockTableScan instance for building queries.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;to_pandas&#x22;" type="&#x22;(self) -> pd.DataFrame&#x22;">
  Read entire table as pandas DataFrame.

  <PySourceCode>
    ```python
    def to_pandas(self) -> pd.DataFrame:
        """Read entire table as pandas DataFrame.

        Returns:
            DataFrame with all table data.

        """
        return self.conn.execute(f"SELECT * FROM {self.name}").df()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;pandas.DataFrame&#x22;">
    DataFrame with all table data.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;to_arrow&#x22;" type="&#x22;(self) -> pa.Table&#x22;">
  Read entire table as PyArrow Table.

  <PySourceCode>
    ```python
    def to_arrow(self) -> pa.Table:
        """Read entire table as PyArrow Table.

        Returns:
            PyArrow Table with all table data.

        """
        return self.conn.execute(f"SELECT * FROM {self.name}").arrow()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;pyarrow.Table&#x22;">
    PyArrow Table with all table data.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;count&#x22;" type="&#x22;(self) -> int&#x22;">
  Return number of rows in table.

  <PySourceCode>
    ```python
    def count(self) -> int:
        """Return number of rows in table.

        Returns:
            Integer row count.

        """
        result = self.conn.execute(f"SELECT COUNT(*) FROM {self.name}").fetchone()
        return result[0] if result else 0
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;">
    Integer row count.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;delete_all&#x22;" type="&#x22;(self) -> None&#x22;">
  Delete all rows from table.

  <PySourceCode>
    ```python
    def delete_all(self) -> None:
        """Delete all rows from table."""
        self.conn.execute(f"DELETE FROM {self.name}")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;drop&#x22;" type="&#x22;(self) -> None&#x22;">
  Drop the table.

  <PySourceCode>
    ```python
    def drop(self) -> None:
        """Drop the table."""
        self.conn.execute(f"DROP TABLE IF EXISTS {self.name}")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
