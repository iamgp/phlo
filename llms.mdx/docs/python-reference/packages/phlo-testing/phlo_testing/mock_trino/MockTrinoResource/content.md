# MockTrinoResource (/docs/python-reference/packages/phlo-testing/phlo_testing/mock_trino/MockTrinoResource)



Mock Trino resource for testing.

Drop-in replacement for TrinoResource that uses DuckDB as backend.
Enables SQL testing without a real Trino server.

Attributes [#attributes]

<PyAttribute name="&#x22;host&#x22;" type="null" value="&#x22;host&#x22;">
  Hostname (for compatibility).
</PyAttribute>

<PyAttribute name="&#x22;port&#x22;" type="null" value="&#x22;port&#x22;">
  Port number (for compatibility).
</PyAttribute>

<PyAttribute name="&#x22;user&#x22;" type="null" value="&#x22;user&#x22;">
  Username (for compatibility).
</PyAttribute>

<PyAttribute name="&#x22;catalog&#x22;" type="null" value="&#x22;catalog&#x22;">
  Catalog name (for compatibility).
</PyAttribute>

<PyAttribute name="&#x22;trino_schema&#x22;" type="null" value="&#x22;trino_schema&#x22;">
  Schema name (for compatibility).
</PyAttribute>

<PyAttribute name="&#x22;_db&#x22;" type="null" value="&#x22;duckdb.connect(':memory:')&#x22;">
  DuckDB connection for query execution.
</PyAttribute>

<PyAttribute name="&#x22;_tables&#x22;" type="&#x22;dict[str, pd.DataFrame]&#x22;" value="&#x22;{}&#x22;">
  Dictionary of loaded test tables.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, host='localhost', port=8080, user='dagster', catalog='memory', trino_schema=None) -> None&#x22;">
  Initialize mock Trino resource.

  <PySourceCode>
    ```python
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        user: str = "dagster",
        catalog: str = "memory",
        trino_schema: Optional[str] = None,
    ) -> None:
        """Initialize mock Trino resource.

        Args:
            host: Host (ignored, for compatibility).
            port: Port (ignored, for compatibility).
            user: Username (ignored, for compatibility).
            catalog: Catalog name (ignored, for compatibility).
            trino_schema: Schema name (ignored, for compatibility).

        """
        self.host = host
        self.port = port
        self.user = user
        self.catalog = catalog
        self.trino_schema = trino_schema
        self._db = duckdb.connect(":memory:")
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

    <PyParameter name="&#x22;user&#x22;" type="&#x22;str&#x22;" value="&#x22;'dagster'&#x22;">
      Username (ignored, for compatibility).
    </PyParameter>

    <PyParameter name="&#x22;catalog&#x22;" type="&#x22;str&#x22;" value="&#x22;'memory'&#x22;">
      Catalog name (ignored, for compatibility).
    </PyParameter>

    <PyParameter name="&#x22;trino_schema&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Schema name (ignored, for compatibility).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_connection&#x22;" type="&#x22;(self, schema=None, branch=None) -> MockConnection&#x22;">
  Get a connection.

  <PySourceCode>
    ```python
    def get_connection(
        self,
        schema: Optional[str] = None,
        branch: Optional[Literal["main", "dev"]] = None,
    ) -> MockConnection:
        """Get a connection.

        Args:
            schema: Schema to use.
            branch: Branch (ignored, for compatibility).

        Returns:
            MockConnection instance.

        """
        return MockConnection(
            host=self.host,
            port=self.port,
            user=self.user,
            catalog=self.catalog,
            schema=schema or self.trino_schema,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Schema to use.
    </PyParameter>

    <PyParameter name="&#x22;branch&#x22;" type="&#x22;Optional[Literal['main', 'dev']]&#x22;" value="&#x22;None&#x22;">
      Branch (ignored, for compatibility).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.mock_trino.MockConnection&#x22;">
    MockConnection instance.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;connection&#x22;" type="&#x22;(self, schema=None, branch=None) -> Iterator[MockConnection]&#x22;">
  Context manager for a connection.

  <PySourceCode>
    ```python
    @contextmanager
    def connection(
        self,
        schema: Optional[str] = None,
        branch: Optional[Literal["main", "dev"]] = None,
    ) -> Iterator[MockConnection]:
        """Context manager for a connection.

        Args:
            schema: Schema to use.
            branch: Branch (ignored, for compatibility).

        Yields:
            MockConnection instance.

        """
        conn = self.get_connection(schema=schema, branch=branch)
        try:
            yield conn
        finally:
            conn.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Schema to use.
    </PyParameter>

    <PyParameter name="&#x22;branch&#x22;" type="&#x22;Optional[Literal['main', 'dev']]&#x22;" value="&#x22;None&#x22;">
      Branch (ignored, for compatibility).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Iterator[phlo_testing.mock_trino.MockConnection]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;cursor&#x22;" type="&#x22;(self, schema=None, branch=None) -> MockCursor&#x22;">
  Get a cursor.

  <PySourceCode>
    ```python
    def cursor(
        self,
        schema: Optional[str] = None,
        branch: Optional[Literal["main", "dev"]] = None,
    ) -> MockCursor:
        """Get a cursor.

        Args:
            schema: Schema to use.
            branch: Branch (ignored, for compatibility).

        Returns:
            MockCursor instance.

        """
        return MockCursor(self._db)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Schema to use.
    </PyParameter>

    <PyParameter name="&#x22;branch&#x22;" type="&#x22;Optional[Literal['main', 'dev']]&#x22;" value="&#x22;None&#x22;">
      Branch (ignored, for compatibility).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.mock_trino.MockCursor&#x22;">
    MockCursor instance.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, query, schema=None, branch=None) -> list[tuple]&#x22;">
  Execute a query.

  <PySourceCode>
    ```python
    def execute(
        self,
        query: str,
        schema: Optional[str] = None,
        branch: Optional[Literal["main", "dev"]] = None,
    ) -> list[tuple]:
        """Execute a query.

        Args:
            query: SQL query.
            schema: Schema to use.
            branch: Branch (ignored, for compatibility).

        Returns:
            List of result tuples.

        """
        cursor = self.cursor(schema=schema, branch=branch)
        cursor.execute(query)
        return cursor.fetchall()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL query.
    </PyParameter>

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Schema to use.
    </PyParameter>

    <PyParameter name="&#x22;branch&#x22;" type="&#x22;Optional[Literal['main', 'dev']]&#x22;" value="&#x22;None&#x22;">
      Branch (ignored, for compatibility).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of result tuples.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;query_with_schema&#x22;" type="&#x22;(self, query, schema_class, schema=None, branch=None) -> pd.DataFrame&#x22;">
  Execute a query and apply types from a Pandera schema.

  This eliminates manual type conversion boilerplate in quality checks.
  The DataFrame types are automatically coerced based on schema annotations.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > from phlo\_testing import MockTrinoResource
    > > > from workflows.schemas.orders import FactOrders
    > > > trino = MockTrinoResource()
    > > > df = trino.query\_with\_schema(
    > > > ...     "SELECT \* FROM gold.fct\_orders",
    > > > ...     FactOrders,
    > > > ... )
    > > >
    > > > Types are now correct for validation [#types-are-now-correct-for-validation]
  </Callout>

  <PySourceCode>
    ```python
    def query_with_schema(
        self,
        query: str,
        schema_class: type[Any],
        schema: Optional[str] = None,
        branch: Optional[Literal["main", "dev"]] = None,
    ) -> pd.DataFrame:
        """Execute a query and apply types from a Pandera schema.

        This eliminates manual type conversion boilerplate in quality checks.
        The DataFrame types are automatically coerced based on schema annotations.

        Args:
            query: SQL query.
            schema_class: Pandera DataFrameModel class with type annotations.
            schema: Schema to use.
            branch: Branch (ignored, for compatibility).

        Returns:
            DataFrame with types coerced according to schema.

        Example:
            >>> from phlo_testing import MockTrinoResource
            >>> from workflows.schemas.orders import FactOrders
            >>> trino = MockTrinoResource()
            >>> df = trino.query_with_schema(
            ...     "SELECT * FROM gold.fct_orders",
            ...     FactOrders,
            ... )
            >>> # Types are now correct for validation

        """
        from phlo_trino.type_mapping import apply_schema_types

        cursor = self.cursor(schema=schema, branch=branch)
        cursor.execute(query)
        df = cursor.fetchdf()

        # Apply schema-aware type conversions
        return apply_schema_types(df, schema_class)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL query.
    </PyParameter>

    <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;type[Any]&#x22;" value="undefined">
      Pandera DataFrameModel class with type annotations.
    </PyParameter>

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Schema to use.
    </PyParameter>

    <PyParameter name="&#x22;branch&#x22;" type="&#x22;Optional[Literal['main', 'dev']]&#x22;" value="&#x22;None&#x22;">
      Branch (ignored, for compatibility).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;pandas.DataFrame&#x22;">
    DataFrame with types coerced according to schema.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;load_table&#x22;" type="&#x22;(self, table_name, df) -> None&#x22;">
  Load a DataFrame as a test table.

  Useful for setting up test data.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > trino = MockTrinoResource()
    > > > df = pd.DataFrame(\{"id": \[1, 2], "name": \["Alice", "Bob"]})
    > > > trino.load\_table("test.users", df)
    > > > cursor = trino.cursor()
    > > > cursor.execute("SELECT \* FROM test.users")
  </Callout>

  <PySourceCode>
    ```python
    def load_table(self, table_name: str, df: pd.DataFrame) -> None:
        """Load a DataFrame as a test table.

        Useful for setting up test data.

        Args:
            table_name: Name of table to create.
            df: DataFrame with data.

        Example:
            >>> trino = MockTrinoResource()
            >>> df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
            >>> trino.load_table("test.users", df)
            >>> cursor = trino.cursor()
            >>> cursor.execute("SELECT * FROM test.users")

        """
        self._tables[table_name] = df

        # Register DataFrame with DuckDB
        self._db.register(table_name.replace(".", "_"), df)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of table to create.
    </PyParameter>

    <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
      DataFrame with data.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_table&#x22;" type="&#x22;(self, table_name) -> Optional[pd.DataFrame]&#x22;">
  Get a loaded test table.

  <PySourceCode>
    ```python
    def get_table(self, table_name: str) -> Optional[pd.DataFrame]:
        """Get a loaded test table.

        Args:
            table_name: Name of table.

        Returns:
            DataFrame if table exists, None otherwise.

        """
        return self._tables.get(table_name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of table.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Optional&#x22;">
    DataFrame if table exists, None otherwise.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;list_tables&#x22;" type="&#x22;(self, schema=None) -> list[str]&#x22;">
  List available tables.

  <PySourceCode>
    ```python
    def list_tables(self, schema: Optional[str] = None) -> list[str]:
        """List available tables.

        Args:
            schema: Schema to list (ignored).

        Returns:
            List of table names.

        """
        return list(self._tables.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Schema to list (ignored).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of table names.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;close&#x22;" type="&#x22;(self) -> None&#x22;">
  Close all connections.

  <PySourceCode>
    ```python
    def close(self) -> None:
        """Close all connections."""
        if self._db:
            self._db.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__enter__&#x22;" type="&#x22;(self) -> 'MockTrinoResource'&#x22;">
  Context manager entry.

  <PySourceCode>
    ```python
    def __enter__(self) -> "MockTrinoResource":
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

  <PyFunctionReturn type="&#x22;'MockTrinoResource'&#x22;">
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
