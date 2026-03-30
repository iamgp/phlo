# MockConnection (/docs/python-reference/packages/phlo-testing/phlo_testing/mock_trino/MockConnection)



Mock Trino connection backed by DuckDB.

Implements the DB-API 2.0 connection interface.

Attributes [#attributes]

<PyAttribute name="&#x22;_db&#x22;" type="null" value="&#x22;duckdb.connect(':memory:')&#x22;">
  DuckDB connection.
</PyAttribute>

<PyAttribute name="&#x22;catalog&#x22;" type="null" value="&#x22;catalog&#x22;">
  Catalog name (for compatibility).
</PyAttribute>

<PyAttribute name="&#x22;schema&#x22;" type="null" value="&#x22;schema&#x22;">
  Schema name (for compatibility).
</PyAttribute>

<PyAttribute name="&#x22;_tables&#x22;" type="&#x22;dict[str, pd.DataFrame]&#x22;" value="&#x22;{}&#x22;">
  Dictionary of loaded test tables.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, host='localhost', port=8080, user='user', catalog='memory', schema=None) -> None&#x22;">
  Initialize connection.

  <PySourceCode>
    ```python
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        user: str = "user",
        catalog: str = "memory",
        schema: Optional[str] = None,
    ) -> None:
        """Initialize connection.

        Args:
            host: Host (ignored, for compatibility).
            port: Port (ignored, for compatibility).
            user: Username (ignored, for compatibility).
            catalog: Catalog name (ignored, for compatibility).
            schema: Schema name (ignored, for compatibility).

        """
        self._db = duckdb.connect(":memory:")
        self.catalog = catalog
        self.schema = schema
        self._tables: dict[str, pd.DataFrame] = {}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;host&#x22;" type="&#x22;str&#x22;" value="&#x22;'localhost'&#x22;">
      Host (ignored, for compatibility).
    </PyParameter>

    <PyParameter name="&#x22;port&#x22;" type="&#x22;int&#x22;" value="&#x22;8080&#x22;">
      Port (ignored, for compatibility).
    </PyParameter>

    <PyParameter name="&#x22;user&#x22;" type="&#x22;str&#x22;" value="&#x22;'user'&#x22;">
      Username (ignored, for compatibility).
    </PyParameter>

    <PyParameter name="&#x22;catalog&#x22;" type="&#x22;str&#x22;" value="&#x22;'memory'&#x22;">
      Catalog name (ignored, for compatibility).
    </PyParameter>

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Schema name (ignored, for compatibility).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;cursor&#x22;" type="&#x22;(self) -> MockCursor&#x22;">
  Create a cursor.

  <PySourceCode>
    ```python
    def cursor(self) -> MockCursor:
        """Create a cursor.

        Returns:
            MockCursor instance.

        """
        return MockCursor(self._db)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.mock_trino.MockCursor&#x22;">
    MockCursor instance.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, query) -> MockCursor&#x22;">
  Execute a query and return cursor.

  <PySourceCode>
    ```python
    def execute(self, query: str) -> MockCursor:
        """Execute a query and return cursor.

        Args:
            query: SQL query.

        Returns:
            MockCursor with results.

        """
        cursor = self.cursor()
        cursor.execute(query)
        return cursor
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL query.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.mock_trino.MockCursor&#x22;">
    MockCursor with results.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;commit&#x22;" type="&#x22;(self) -> None&#x22;">
  Commit transaction (no-op in mock).

  <PySourceCode>
    ```python
    def commit(self) -> None:
        """Commit transaction (no-op in mock)."""
        pass
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;rollback&#x22;" type="&#x22;(self) -> None&#x22;">
  Rollback transaction (no-op in mock).

  <PySourceCode>
    ```python
    def rollback(self) -> None:
        """Rollback transaction (no-op in mock)."""
        pass
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;close&#x22;" type="&#x22;(self) -> None&#x22;">
  Close connection.

  <PySourceCode>
    ```python
    def close(self) -> None:
        """Close connection."""
        if self._db:
            self._db.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__enter__&#x22;" type="&#x22;(self) -> 'MockConnection'&#x22;">
  Context manager entry.

  <PySourceCode>
    ```python
    def __enter__(self) -> "MockConnection":
        """Context manager entry.

        Returns:
            Self for context manager use.

        """
        return self
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;'MockConnection'&#x22;">
    Self for context manager use.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__exit__&#x22;" type="&#x22;(self, exc_type, exc_val, exc_tb) -> None&#x22;">
  Context manager exit.

  <PySourceCode>
    ```python
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;exc_type&#x22;" type="&#x22;Any&#x22;" value="null" />

    <PyParameter name="&#x22;exc_val&#x22;" type="&#x22;Any&#x22;" value="null" />

    <PyParameter name="&#x22;exc_tb&#x22;" type="&#x22;Any&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
