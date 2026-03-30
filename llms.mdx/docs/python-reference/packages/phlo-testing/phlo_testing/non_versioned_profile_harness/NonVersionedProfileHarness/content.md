# NonVersionedProfileHarness (/docs/python-reference/packages/phlo-testing/phlo_testing/non_versioned_profile_harness/NonVersionedProfileHarness)



Local DuckDB-backed harness for a non-versioned profile.

Provides methods to ingest data, run dbt transforms, and query results
using DuckDB as the backend.

Attributes [#attributes]

<PyAttribute name="&#x22;project_dir&#x22;" type="&#x22;Path&#x22;" value="null">
  Path to the temporary dbt project directory.
</PyAttribute>

<PyAttribute name="&#x22;duckdb_path&#x22;" type="&#x22;Path&#x22;" value="null">
  Path to the DuckDB database file.
</PyAttribute>

<PyAttribute name="&#x22;dbt_executable&#x22;" type="&#x22;str&#x22;" value="null">
  Path to the dbt executable.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;ingest_rows&#x22;" type="&#x22;(self, table_name, rows) -> None&#x22;">
  Create or replace a raw DuckDB table from row dictionaries.

  <PySourceCode>
    ```python
    def ingest_rows(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        """Create or replace a raw DuckDB table from row dictionaries.

        Args:
            table_name: Schema-qualified table name (e.g., "raw.posts").
            rows: List of dictionaries representing rows.

        Raises:
            ValueError: If table_name is not schema-qualified.

        """
        if "." not in table_name:
            raise ValueError("Expected schema-qualified table name like 'raw.posts'")
        schema_name, table_name_only = table_name.split(".", 1)
        dataframe = pd.DataFrame(rows)
        connection = duckdb.connect(str(self.duckdb_path))
        try:
            connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            connection.register("phlo_ingest_rows", dataframe)
            connection.execute(
                f"CREATE OR REPLACE TABLE {schema_name}.{table_name_only} AS "
                "SELECT * FROM phlo_ingest_rows"
            )
        finally:
            connection.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema-qualified table name (e.g., "raw\.posts").
    </PyParameter>

    <PyParameter name="&#x22;rows&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="undefined">
      List of dictionaries representing rows.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;query&#x22;" type="&#x22;(self, query) -> list[tuple[Any, ...]]&#x22;">
  Execute a DuckDB SQL query against the local profile database.

  <PySourceCode>
    ```python
    def query(self, query: str) -> list[tuple[Any, ...]]:
        """Execute a DuckDB SQL query against the local profile database.

        Args:
            query: SQL query string.

        Returns:
            List of result tuples.

        """
        connection = duckdb.connect(str(self.duckdb_path))
        try:
            return connection.execute(query).fetchall()
        finally:
            connection.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL query string.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of result tuples.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;query_scalar&#x22;" type="&#x22;(self, query) -> Any&#x22;">
  Execute a SQL query and return the first scalar value.

  <PySourceCode>
    ```python
    def query_scalar(self, query: str) -> Any:
        """Execute a SQL query and return the first scalar value.

        Args:
            query: SQL query string.

        Returns:
            First column of first row, or None if no results.

        """
        rows = self.query(query)
        if not rows:
            return None
        return rows[0][0]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL query string.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    First column of first row, or None if no results.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;run_transform&#x22;" type="&#x22;(self) -> Any&#x22;">
  Run the dbt transform project against the local DuckDB profile.

  <PySourceCode>
    ```python
    def run_transform(self) -> Any:
        """Run the dbt transform project against the local DuckDB profile.

        Returns:
            dbt run result.

        """
        from phlo_dbt.transformer import DbtTransformer

        transformer = DbtTransformer(
            context=None,
            logger=get_logger("phlo_testing.non_versioned_profile"),
            project_dir=self.project_dir,
            profiles_dir=self.project_dir,
            target="dev",
            dbt_executable=self.dbt_executable,
        )
        return transformer.run_transform(partition_key=None, parameters={"generate_docs": False})
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    dbt run result.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;cleanup&#x22;" type="&#x22;(self) -> None&#x22;">
  Remove the temporary harness directory unless kept by the caller.

  <PySourceCode>
    ```python
    def cleanup(self) -> None:
        """Remove the temporary harness directory unless kept by the caller."""
        with contextlib.suppress(Exception):
            shutil.rmtree(self.project_dir)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, project_dir, duckdb_path, dbt_executable) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;project_dir&#x22;" type="&#x22;Path&#x22;" value="null" />

    <PyParameter name="&#x22;duckdb_path&#x22;" type="&#x22;Path&#x22;" value="null" />

    <PyParameter name="&#x22;dbt_executable&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
