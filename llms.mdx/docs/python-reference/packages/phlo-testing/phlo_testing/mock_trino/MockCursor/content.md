# MockCursor (/docs/python-reference/packages/phlo-testing/phlo_testing/mock_trino/MockCursor)



Mock Trino cursor backed by DuckDB.

Implements the DB-API 2.0 cursor interface for compatibility
with standard database access patterns.

Attributes [#attributes]

<PyAttribute name="&#x22;_connection&#x22;" type="null" value="&#x22;connection&#x22;">
  DuckDB connection.
</PyAttribute>

<PyAttribute name="&#x22;_result&#x22;" type="null" value="&#x22;None&#x22;">
  Current query result.
</PyAttribute>

<PyAttribute name="&#x22;_description&#x22;" type="null" value="&#x22;None&#x22;">
  Column metadata from last query.
</PyAttribute>

<PyAttribute name="&#x22;_row_index&#x22;" type="null" value="&#x22;0&#x22;">
  Current row position.
</PyAttribute>

<PyAttribute name="&#x22;description&#x22;" type="&#x22;Optional[list]&#x22;" value="null">
  Get column metadata.
</PyAttribute>

<PyAttribute name="&#x22;rowcount&#x22;" type="&#x22;int&#x22;" value="null">
  Get number of affected rows.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, connection) -> None&#x22;">
  Initialize cursor.

  <PySourceCode>
    ```python
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        """Initialize cursor.

        Args:
            connection: DuckDB connection to use for queries.

        """
        self._connection = connection
        self._result = None
        self._description = None
        self._row_index = 0
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;connection&#x22;" type="&#x22;duckdb.DuckDBPyConnection&#x22;" value="undefined">
      DuckDB connection to use for queries.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, query, params=None) -> 'MockCursor'&#x22;">
  Execute a SQL query.

  <PySourceCode>
    ```python
    def execute(self, query: str, params: Optional[tuple] = None) -> "MockCursor":
        """Execute a SQL query.

        Args:
            query: SQL query string.
            params: Optional parameters (not fully supported).

        Returns:
            Self for method chaining.

        Raises:
            RuntimeError: If query fails.

        """
        try:
            # Translate Trino SQL to DuckDB if needed
            query = self._translate_query(query)

            # Execute query
            result = self._connection.execute(query)
            self._result = result

            # Get column names and types
            try:
                # Try to get columns from result
                cols = result.columns
                if cols:
                    self._description = [
                        (name, "VARCHAR")  # Simplified type mapping
                        for name in cols
                    ]
                else:
                    self._description = None
            except (AttributeError, TypeError):
                # Fallback if no columns attribute
                self._description = None

            self._row_index = 0
            return self

        except Exception as e:
            logger.warning("mock_trino_query_execution_failed", query=query, exc_info=True)
            raise RuntimeError(f"Query execution failed: {e}") from e
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL query string.
    </PyParameter>

    <PyParameter name="&#x22;params&#x22;" type="&#x22;Optional[tuple]&#x22;" value="&#x22;None&#x22;">
      Optional parameters (not fully supported).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;'MockCursor'&#x22;">
    Self for method chaining.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;fetchall&#x22;" type="&#x22;(self) -> list[tuple]&#x22;">
  Fetch all results.

  <PySourceCode>
    ```python
    def fetchall(self) -> list[tuple]:
        """Fetch all results.

        Returns:
            List of tuples representing rows.

        """
        if self._result is None:
            return []

        rows = self._result.fetchall()
        self._row_index = len(rows)
        return rows
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of tuples representing rows.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;fetchone&#x22;" type="&#x22;(self) -> Optional[tuple]&#x22;">
  Fetch one result.

  <PySourceCode>
    ```python
    def fetchone(self) -> Optional[tuple]:
        """Fetch one result.

        Returns:
            Single row as tuple, or None if no more rows.

        """
        if self._result is None:
            return None

        row = self._result.fetchone()
        if row is not None:
            self._row_index += 1
        return row
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Optional&#x22;">
    Single row as tuple, or None if no more rows.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;fetchmany&#x22;" type="&#x22;(self, size=1) -> list[tuple]&#x22;">
  Fetch multiple results.

  <PySourceCode>
    ```python
    def fetchmany(self, size: int = 1) -> list[tuple]:
        """Fetch multiple results.

        Args:
            size: Number of rows to fetch.

        Returns:
            List of tuples.

        """
        if self._result is None:
            return []

        rows = self._result.fetchmany(size)
        self._row_index += len(rows)
        return rows
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;size&#x22;" type="&#x22;int&#x22;" value="&#x22;1&#x22;">
      Number of rows to fetch.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of tuples.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;fetchdf&#x22;" type="&#x22;(self) -> pd.DataFrame&#x22;">
  Fetch all results as DataFrame.

  <PySourceCode>
    ```python
    def fetchdf(self) -> pd.DataFrame:
        """Fetch all results as DataFrame.

        Returns:
            DataFrame with query results.

        """
        if self._result is None:
            return pd.DataFrame()

        return self._result.df()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;pandas.DataFrame&#x22;">
    DataFrame with query results.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;close&#x22;" type="&#x22;(self) -> None&#x22;">
  Close cursor.

  <PySourceCode>
    ```python
    def close(self) -> None:
        """Close cursor."""
        self._result = None
        self._description = None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_translate_query&#x22;" type="&#x22;(query) -> str&#x22;">
  Translate Trino SQL to DuckDB SQL.

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    Most Trino SQL is compatible with DuckDB, but we handle some
    common differences here.
  </Callout>

  <PySourceCode>
    ```python
    @staticmethod
    def _translate_query(query: str) -> str:
        """Translate Trino SQL to DuckDB SQL.

        Args:
            query: Trino SQL query.

        Returns:
            DuckDB SQL query.

        Note:
            Most Trino SQL is compatible with DuckDB, but we handle some
            common differences here.

        """
        # Replace common Trino functions with DuckDB equivalents

        # For now, most Trino queries work directly in DuckDB
        return query
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
      Trino SQL query.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    DuckDB SQL query.
  </PyFunctionReturn>
</PyFunction>
