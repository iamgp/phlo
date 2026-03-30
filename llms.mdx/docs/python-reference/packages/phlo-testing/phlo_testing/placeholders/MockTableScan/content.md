# MockTableScan (/docs/python-reference/packages/phlo-testing/phlo_testing/placeholders/MockTableScan)



Mock Iceberg table scan for querying.

Implements filter and limit operations for table queries.

Attributes [#attributes]

<PyAttribute name="&#x22;table_name&#x22;" type="null" value="&#x22;table_name&#x22;">
  Name of table being scanned.
</PyAttribute>

<PyAttribute name="&#x22;conn&#x22;" type="null" value="&#x22;conn&#x22;">
  DuckDB connection.
</PyAttribute>

<PyAttribute name="&#x22;_filter_expr&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;_limit&#x22;" type="&#x22;Optional[int]&#x22;" value="&#x22;None&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, table_name, conn)&#x22;">
  Initialize table scan.

  <PySourceCode>
    ```python
    def __init__(self, table_name: str, conn: "duckdb.DuckDBPyConnection"):
        """Initialize table scan.

        Args:
            table_name: Name of table to scan.
            conn: DuckDB connection for query execution.

        """
        self.table_name = table_name
        self.conn = conn
        self._filter_expr: Optional[str] = None
        self._limit: Optional[int] = None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of table to scan.
    </PyParameter>

    <PyParameter name="&#x22;conn&#x22;" type="&#x22;duckdb.DuckDBPyConnection&#x22;" value="undefined">
      DuckDB connection for query execution.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;filter&#x22;" type="&#x22;(self, expr) -> MockTableScan&#x22;">
  Add WHERE clause filter (SQL syntax).

  <PySourceCode>
    ```python
    def filter(self, expr: str) -> "MockTableScan":
        """Add WHERE clause filter (SQL syntax).

        Args:
            expr: SQL WHERE clause expression.

        Returns:
            Self for method chaining.

        """
        self._filter_expr = expr
        return self
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;expr&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL WHERE clause expression.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.placeholders.MockTableScan&#x22;">
    Self for method chaining.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;limit&#x22;" type="&#x22;(self, n) -> MockTableScan&#x22;">
  Limit number of rows.

  <PySourceCode>
    ```python
    def limit(self, n: int) -> "MockTableScan":
        """Limit number of rows.

        Args:
            n: Maximum number of rows to return.

        Returns:
            Self for method chaining.

        """
        self._limit = n
        return self
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;n&#x22;" type="&#x22;int&#x22;" value="undefined">
      Maximum number of rows to return.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.placeholders.MockTableScan&#x22;">
    Self for method chaining.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;to_pandas&#x22;" type="&#x22;(self) -> pd.DataFrame&#x22;">
  Execute scan and return pandas DataFrame.

  <PySourceCode>
    ```python
    def to_pandas(self) -> pd.DataFrame:
        """Execute scan and return pandas DataFrame.

        Returns:
            DataFrame with query results.

        """
        query = f"SELECT * FROM {self.table_name}"
        if self._filter_expr:
            query += f" WHERE {self._filter_expr}"
        if self._limit:
            query += f" LIMIT {self._limit}"
        return self.conn.execute(query).df()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;pandas.DataFrame&#x22;">
    DataFrame with query results.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;to_arrow&#x22;" type="&#x22;(self) -> pa.Table&#x22;">
  Execute scan and return PyArrow Table.

  <PySourceCode>
    ```python
    def to_arrow(self) -> pa.Table:
        """Execute scan and return PyArrow Table.

        Returns:
            PyArrow Table with query results.

        """
        query = f"SELECT * FROM {self.table_name}"
        if self._filter_expr:
            query += f" WHERE {self._filter_expr}"
        if self._limit:
            query += f" LIMIT {self._limit}"
        return self.conn.execute(query).arrow()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;pyarrow.Table&#x22;">
    PyArrow Table with query results.
  </PyFunctionReturn>
</PyFunction>
