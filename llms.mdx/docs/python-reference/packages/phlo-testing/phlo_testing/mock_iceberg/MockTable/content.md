# MockTable (/docs/python-reference/packages/phlo-testing/phlo_testing/mock_iceberg/MockTable)



Mock Iceberg table backed by DuckDB.

Stores metadata in Python, actual data in DuckDB in-memory database.

Attributes [#attributes]

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Table identifier (e.g., "raw\.users").
</PyAttribute>

<PyAttribute name="&#x22;schema&#x22;" type="&#x22;Union[dict[str, str], Any]&#x22;" value="null">
  Schema dict or PyIceberg Schema object.
</PyAttribute>

<PyAttribute name="&#x22;_db&#x22;" type="&#x22;duckdb.DuckDBPyConnection&#x22;" value="null">
  DuckDB connection for data storage.
</PyAttribute>

<PyAttribute name="&#x22;_catalog&#x22;" type="&#x22;Optional['MockIcebergCatalog']&#x22;" value="&#x22;None&#x22;">
  Reference to parent catalog.
</PyAttribute>

<PyAttribute name="&#x22;full_name&#x22;" type="&#x22;str&#x22;" value="null">
  Get full table name with namespace.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__post_init__&#x22;" type="&#x22;(self) -> None&#x22;">
  Initialize table in DuckDB.

  <PySourceCode>
    ```python
    def __post_init__(self) -> None:
        """Initialize table in DuckDB."""
        self._create_duckdb_table()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_create_duckdb_table&#x22;" type="&#x22;(self) -> None&#x22;">
  Create the actual table in DuckDB.

  <PySourceCode>
    ```python
    def _create_duckdb_table(self) -> None:
        """Create the actual table in DuckDB."""
        namespace, table_name = self.name.split(".")
        full_name = f"{namespace}_{table_name}"

        # Build CREATE TABLE statement from schema
        columns = []

        if isinstance(self.schema, dict):
            # Simple dict schema: {"col_name": "type_string"}
            for col_name, col_type in self.schema.items():
                duckdb_type = _normalize_type(col_type)
                columns.append(f"{col_name} {duckdb_type}")
        else:
            # PyIceberg Schema object
            for field in self.schema.fields:
                duckdb_type = _normalize_type(str(field.type))
                nullable = "NULL" if field.optional else "NOT NULL"
                columns.append(f"{field.name} {duckdb_type} {nullable}")

        create_stmt = f"CREATE TABLE {full_name} ({', '.join(columns)})"
        try:
            self._db.execute(create_stmt)
        except duckdb.CatalogException:
            # Table already exists
            logger.debug(
                "mock_iceberg_create_table_exists",
                table_name=self.name,
                duckdb_table=full_name,
            )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;append&#x22;" type="&#x22;(self, df) -> None&#x22;">
  Append DataFrame to table.

  <PySourceCode>
    ```python
    def append(self, df: pd.DataFrame) -> None:
        """Append DataFrame to table.

        Args:
            df: Data to append.

        Raises:
            ValueError: If schema doesn't match.

        """
        namespace, table_name = self.name.split(".")
        full_name = f"{namespace}_{table_name}"

        # Validate schema
        self._validate_schema(df)

        # Insert into DuckDB
        self._db.from_df(df).insert_into(full_name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
      Data to append.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;overwrite&#x22;" type="&#x22;(self, df) -> None&#x22;">
  Replace table contents with DataFrame.

  <PySourceCode>
    ```python
    def overwrite(self, df: pd.DataFrame) -> None:
        """Replace table contents with DataFrame.

        Args:
            df: Data to replace with.

        """
        namespace, table_name = self.name.split(".")
        full_name = f"{namespace}_{table_name}"

        # Validate schema
        self._validate_schema(df)

        # Truncate and insert
        self._db.execute(f"DELETE FROM {full_name}")
        self._db.from_df(df).insert_into(full_name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
      Data to replace with.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;scan&#x22;" type="&#x22;(self) -> 'MockTableScan'&#x22;">
  Scan table data.

  <PySourceCode>
    ```python
    def scan(self) -> "MockTableScan":
        """Scan table data.

        Returns:
            MockTableScan object for querying.

        """
        return MockTableScan(self)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;'MockTableScan'&#x22;">
    MockTableScan object for querying.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_validate_schema&#x22;" type="&#x22;(self, df) -> None&#x22;">
  Validate DataFrame schema against table schema.

  <PySourceCode>
    ```python
    def _validate_schema(self, df: pd.DataFrame) -> None:
        """Validate DataFrame schema against table schema.

        Args:
            df: DataFrame to validate.

        Raises:
            ValueError: If schema doesn't match.

        """
        df_cols = set(df.columns)

        if isinstance(self.schema, dict):
            table_cols = set(self.schema.keys())
        else:
            # PyIceberg Schema
            table_cols = {field.name for field in self.schema.fields}

        if df_cols != table_cols:
            missing = table_cols - df_cols
            extra = df_cols - table_cols
            msg = f"Schema mismatch for {self.name}"
            if missing:
                msg += f"\nMissing columns: {missing}"
            if extra:
                msg += f"\nExtra columns: {extra}"
            raise ValueError(msg)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
      DataFrame to validate.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, name, schema, _db, _catalog=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Union[dict[str, str], Any]&#x22;" value="null" />

    <PyParameter name="&#x22;_db&#x22;" type="&#x22;duckdb.DuckDBPyConnection&#x22;" value="null" />

    <PyParameter name="&#x22;_catalog&#x22;" type="&#x22;Optional['MockIcebergCatalog']&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
