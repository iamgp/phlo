# MockIcebergCatalog (/docs/python-reference/packages/phlo-testing/phlo_testing/placeholders/MockIcebergCatalog)



Mock Iceberg catalog for testing without Docker.

Provides a PyIceberg-compatible API backed by in-memory DuckDB.
Perfect for fast unit tests without Docker infrastructure.

Features:

* In-memory DuckDB backend (no persistence)
* PyIceberg schema support
* Create/drop tables
* Append data (DataFrame or Arrow)
* Scan with filters and limits
* Less than 5 second test execution

Limitations:

* No actual Iceberg format files (uses DuckDB tables)
* No time travel/snapshots
* No partitioning
* Schema evolution not implemented
* Good for unit tests, not production

Example:

> > > with mock\_iceberg\_catalog() as catalog:
> > > ...     # Create table from PyIceberg schema
> > > ...     table = catalog.create\_table("test.my\_table", schema=my\_schema)
> > > ...     # Append data
> > > ...     df = pd.DataFrame(\[\{"id": "1", "value": 42}])
> > > ...     table.append(df)
> > > ...     # Query data
> > > ...     result = table.scan().to\_pandas()
> > > ...     assert len(result) == 1

Status: Fully implemented (using DuckDB backend)

Attributes [#attributes]

<PyAttribute name="&#x22;conn&#x22;" type="null" value="&#x22;duckdb.connect(':memory:')&#x22;" />

<PyAttribute name="&#x22;tables&#x22;" type="&#x22;Dict[str, MockIcebergTable]&#x22;" value="&#x22;{}&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self)&#x22;">
  Initialize mock Iceberg catalog with in-memory DuckDB.

  <PySourceCode>
    ```python
    def __init__(self):
        """Initialize mock Iceberg catalog with in-memory DuckDB.

        Raises:
            ImportError: If DuckDB or PyArrow are not installed.

        """
        if not ICEBERG_DEPS_AVAILABLE:
            raise ImportError(
                "DuckDB and PyArrow are required for MockIcebergCatalog. "
                "Install with: pip install duckdb pyarrow"
            )

        # Create in-memory DuckDB connection
        self.conn = duckdb.connect(":memory:")
        self.tables: Dict[str, MockIcebergTable] = {}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;create_table&#x22;" type="&#x22;(self, name, schema, if_not_exists=False) -> MockIcebergTable&#x22;">
  Create a new table.

  <PySourceCode>
    ```python
    def create_table(
        self,
        name: str,
        schema: Schema,
        if_not_exists: bool = False,
    ) -> MockIcebergTable:
        """Create a new table.

        Args:
            name: Table name (can include namespace like "raw.table_name").
            schema: PyIceberg Schema object.
            if_not_exists: If True, don't error if table exists.

        Returns:
            MockIcebergTable instance.

        Raises:
            ValueError: If table already exists and if_not_exists=False.

        """
        # Sanitize table name for DuckDB (replace dots with underscores)
        duckdb_name = name.replace(".", "_")

        if duckdb_name in self.tables:
            if if_not_exists:
                return self.tables[duckdb_name]
            raise ValueError(f"Table {name} already exists")

        table = MockIcebergTable(duckdb_name, schema, self.conn)
        self.tables[duckdb_name] = table
        return table
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name (can include namespace like "raw\.table\_name").
    </PyParameter>

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Schema&#x22;" value="undefined">
      PyIceberg Schema object.
    </PyParameter>

    <PyParameter name="&#x22;if_not_exists&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
      If True, don't error if table exists.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.placeholders.MockIcebergTable&#x22;">
    MockIcebergTable instance.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;load_table&#x22;" type="&#x22;(self, name) -> MockIcebergTable&#x22;">
  Load an existing table.

  <PySourceCode>
    ```python
    def load_table(self, name: str) -> MockIcebergTable:
        """Load an existing table.

        Args:
            name: Table name.

        Returns:
            MockIcebergTable instance.

        Raises:
            KeyError: If table doesn't exist.

        """
        duckdb_name = name.replace(".", "_")
        if duckdb_name not in self.tables:
            raise KeyError(f"Table {name} not found. Available tables: {list(self.tables.keys())}")
        return self.tables[duckdb_name]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.placeholders.MockIcebergTable&#x22;">
    MockIcebergTable instance.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;list_tables&#x22;" type="&#x22;(self) -> List[str]&#x22;">
  List all tables in catalog.

  <PySourceCode>
    ```python
    def list_tables(self) -> List[str]:
        """List all tables in catalog.

        Returns:
            List of table names.

        """
        return list(self.tables.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.List&#x22;">
    List of table names.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;drop_table&#x22;" type="&#x22;(self, name) -> None&#x22;">
  Drop a table.

  <PySourceCode>
    ```python
    def drop_table(self, name: str) -> None:
        """Drop a table.

        Args:
            name: Table name.

        """
        duckdb_name = name.replace(".", "_")
        if duckdb_name in self.tables:
            self.tables[duckdb_name].drop()
            del self.tables[duckdb_name]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;close&#x22;" type="&#x22;(self) -> None&#x22;">
  Close DuckDB connection.

  <PySourceCode>
    ```python
    def close(self) -> None:
        """Close DuckDB connection."""
        self.conn.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__enter__&#x22;" type="&#x22;(self)&#x22;">
  Context manager entry.

  <PySourceCode>
    ```python
    def __enter__(self):
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

  <PyFunctionReturn type="null">
    Self for context manager use.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__exit__&#x22;" type="&#x22;(self, exc_type, exc_val, exc_tb)&#x22;">
  Context manager exit - cleanup.

  <PySourceCode>
    ```python
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup."""
        self.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;exc_type&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;exc_val&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;exc_tb&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>
