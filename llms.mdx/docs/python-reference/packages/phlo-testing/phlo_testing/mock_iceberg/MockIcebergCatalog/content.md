# MockIcebergCatalog (/docs/python-reference/packages/phlo-testing/phlo_testing/mock_iceberg/MockIcebergCatalog)



In-memory Iceberg catalog mock using DuckDB backend.

Implements a subset of PyIceberg's Catalog interface for testing.
Tables are stored in DuckDB with metadata tracked in Python dicts.

Attributes [#attributes]

<PyAttribute name="&#x22;_db&#x22;" type="null" value="&#x22;duckdb.connect(':memory:')&#x22;">
  DuckDB connection for data storage.
</PyAttribute>

<PyAttribute name="&#x22;_tables&#x22;" type="&#x22;dict[str, MockTable]&#x22;" value="&#x22;{}&#x22;">
  Dictionary of table metadata.
</PyAttribute>

<PyAttribute name="&#x22;_namespaces&#x22;" type="&#x22;set[str]&#x22;" value="&#x22;set()&#x22;">
  Set of namespace names.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self) -> None&#x22;">
  Initialize in-memory DuckDB catalog.

  <PySourceCode>
    ```python
    def __init__(self) -> None:
        """Initialize in-memory DuckDB catalog."""
        self._db = duckdb.connect(":memory:")
        self._tables: dict[str, MockTable] = {}
        self._namespaces: set[str] = set()

        # Create default namespaces
        for ns in ["raw", "bronze", "silver", "gold", "marts"]:
            self.create_namespace(ns)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;create_namespace&#x22;" type="&#x22;(self, namespace) -> None&#x22;">
  Create a namespace.

  <PySourceCode>
    ```python
    def create_namespace(self, namespace: str) -> None:
        """Create a namespace.

        Args:
            namespace: Namespace name.

        Raises:
            ValueError: If namespace already exists.

        """
        if namespace in self._namespaces:
            raise ValueError(f"Namespace {namespace} already exists")

        self._namespaces.add(namespace)

        # Create schema in DuckDB
        try:
            self._db.execute(f'CREATE SCHEMA "{namespace}"')
        except duckdb.CatalogException:
            # Schema might already exist
            logger.debug("mock_iceberg_namespace_exists", namespace=namespace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;namespace&#x22;" type="&#x22;str&#x22;" value="undefined">
      Namespace name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;drop_namespace&#x22;" type="&#x22;(self, namespace) -> None&#x22;">
  Drop a namespace.

  <PySourceCode>
    ```python
    def drop_namespace(self, namespace: str) -> None:
        """Drop a namespace.

        Args:
            namespace: Namespace name.

        """
        self._namespaces.discard(namespace)
        try:
            self._db.execute(f'DROP SCHEMA IF EXISTS "{namespace}"')
        except duckdb.CatalogException:
            logger.debug("mock_iceberg_drop_namespace_ignored", namespace=namespace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;namespace&#x22;" type="&#x22;str&#x22;" value="undefined">
      Namespace name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;create_table&#x22;" type="&#x22;(self, identifier, schema, partition_spec=None) -> MockTable&#x22;">
  Create a new table.

  <PySourceCode>
    ```python
    def create_table(
        self,
        identifier: str,
        schema: Union[dict[str, str], Any],
        partition_spec: Optional[Sequence[tuple[str, str]]] = None,
    ) -> MockTable:
        """Create a new table.

        Args:
            identifier: Table name (namespace.table).
            schema: Schema dict like {"col": "type"} or PyIceberg Schema.
            partition_spec: Optional partitioning (not fully supported).

        Returns:
            MockTable instance.

        Raises:
            ValueError: If table already exists.

        """
        if identifier in self._tables:
            raise ValueError(f"Table {identifier} already exists")

        # Extract namespace and ensure it exists
        namespace = identifier.split(".")[0]
        if namespace not in self._namespaces:
            self.create_namespace(namespace)

        table = MockTable(
            name=identifier,
            schema=schema,
            _db=self._db,
            _catalog=self,
        )

        self._tables[identifier] = table
        return table
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;identifier&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name (namespace.table).
    </PyParameter>

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Union[dict[str, str], Any]&#x22;" value="undefined">
      Schema dict like \{"col": "type"} or PyIceberg Schema.
    </PyParameter>

    <PyParameter name="&#x22;partition_spec&#x22;" type="&#x22;Optional[Sequence[tuple[str, str]]]&#x22;" value="&#x22;None&#x22;">
      Optional partitioning (not fully supported).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.mock_iceberg.MockTable&#x22;">
    MockTable instance.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;load_table&#x22;" type="&#x22;(self, identifier) -> MockTable&#x22;">
  Load an existing table.

  <PySourceCode>
    ```python
    def load_table(self, identifier: str) -> MockTable:
        """Load an existing table.

        Args:
            identifier: Table name (namespace.table).

        Returns:
            MockTable instance.

        Raises:
            ValueError: If table doesn't exist.

        """
        if identifier not in self._tables:
            raise ValueError(f"Table {identifier} not found")

        return self._tables[identifier]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;identifier&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name (namespace.table).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.mock_iceberg.MockTable&#x22;">
    MockTable instance.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;drop_table&#x22;" type="&#x22;(self, identifier) -> None&#x22;">
  Drop a table.

  <PySourceCode>
    ```python
    def drop_table(self, identifier: str) -> None:
        """Drop a table.

        Args:
            identifier: Table name (namespace.table).

        """
        if identifier in self._tables:
            table = self._tables.pop(identifier)
            try:
                self._db.execute(f"DROP TABLE IF EXISTS {table.full_name}")
            except duckdb.CatalogException:
                logger.debug(
                    "mock_iceberg_drop_table_ignored",
                    table_identifier=identifier,
                    duckdb_table=table.full_name,
                )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;identifier&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name (namespace.table).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_tables&#x22;" type="&#x22;(self, namespace) -> list[str]&#x22;">
  List tables in a namespace.

  <PySourceCode>
    ```python
    def list_tables(self, namespace: str) -> list[str]:
        """List tables in a namespace.

        Args:
            namespace: Namespace name.

        Returns:
            List of table identifiers.

        """
        return [
            identifier
            for identifier in self._tables.keys()
            if identifier.startswith(f"{namespace}.")
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;namespace&#x22;" type="&#x22;str&#x22;" value="undefined">
      Namespace name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of table identifiers.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;list_namespaces&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List all namespaces.

  <PySourceCode>
    ```python
    def list_namespaces(self) -> list[str]:
        """List all namespaces.

        Returns:
            List of namespace names.

        """
        return sorted(self._namespaces)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of namespace names.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;rename_table&#x22;" type="&#x22;(self, old_identifier, new_identifier) -> None&#x22;">
  Rename a table.

  <PySourceCode>
    ```python
    def rename_table(self, old_identifier: str, new_identifier: str) -> None:
        """Rename a table.

        Args:
            old_identifier: Current table name.
            new_identifier: New table name.

        Raises:
            ValueError: If table doesn't exist.

        """
        if old_identifier not in self._tables:
            raise ValueError(f"Table {old_identifier} not found")

        table = self._tables.pop(old_identifier)
        table.name = new_identifier
        self._tables[new_identifier] = table

        # Rename in DuckDB
        old_full = old_identifier.replace(".", "_")
        new_full = new_identifier.replace(".", "_")
        try:
            self._db.execute(f"ALTER TABLE {old_full} RENAME TO {new_full}")
        except duckdb.CatalogException:
            logger.warning(
                "mock_iceberg_rename_duckdb_failed",
                old_identifier=old_identifier,
                new_identifier=new_identifier,
                exc_info=True,
            )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;old_identifier&#x22;" type="&#x22;str&#x22;" value="undefined">
      Current table name.
    </PyParameter>

    <PyParameter name="&#x22;new_identifier&#x22;" type="&#x22;str&#x22;" value="undefined">
      New table name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;table_exists&#x22;" type="&#x22;(self, identifier) -> bool&#x22;">
  Check if a table exists.

  <PySourceCode>
    ```python
    def table_exists(self, identifier: str) -> bool:
        """Check if a table exists.

        Args:
            identifier: Table name (namespace.table).

        Returns:
            True if table exists.

        """
        return identifier in self._tables
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;identifier&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name (namespace.table).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if table exists.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;transaction&#x22;" type="&#x22;(self) -> Iterator[None]&#x22;">
  Context manager for transactions (no-op in mock).

  <PySourceCode>
    ```python
    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Context manager for transactions (no-op in mock).

        Yields:
            None

        """
        try:
            yield
        except Exception:
            logger.warning("mock_iceberg_transaction_failed", exc_info=True)
            raise
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Iterator[None]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;close&#x22;" type="&#x22;(self) -> None&#x22;">
  Close the database connection.

  <PySourceCode>
    ```python
    def close(self) -> None:
        """Close the database connection."""
        if self._db:
            self._db.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__enter__&#x22;" type="&#x22;(self) -> 'MockIcebergCatalog'&#x22;">
  Context manager entry.

  <PySourceCode>
    ```python
    def __enter__(self) -> "MockIcebergCatalog":
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

  <PyFunctionReturn type="&#x22;'MockIcebergCatalog'&#x22;">
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
