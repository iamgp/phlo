# mock_iceberg (/docs/python-reference/packages/phlo-testing/phlo_testing/mock_iceberg)



Mock Iceberg catalog backed by DuckDB for fast unit testing.

Implements a subset of PyIceberg's Catalog interface using an in-memory
DuckDB database, enabling tests to run without the full Iceberg/Nessie stack.

Example:

> > > catalog = MockIcebergCatalog()
> > >
> > > Use with any schema dict like {"id": "int", "name": "string"} [#use-with-any-schema-dict-like-id-int-name-string]
> > >
> > > table = catalog.create\_table("raw\.users", schema=\{"id": "int", "name": "string"})
> > > df = pd.DataFrame(\{"id": \[1, 2], "name": \["Alice", "Bob"]})
> > > table.append(df)
> > > result = table.scan().to\_pandas()

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;MockTable&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/mock_iceberg/MockTable&#x22;" />

      <Card title="&#x22;MockTableScan&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/mock_iceberg/MockTableScan&#x22;" />

      <Card title="&#x22;MockIcebergCatalog&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/mock_iceberg/MockIcebergCatalog&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_normalize_type&#x22;" type="&#x22;(dtype) -> str&#x22;">
      Normalize type string to DuckDB type.

      Handles PyIceberg types, Python types, and plain strings.

      <PySourceCode>
        ```python
        def _normalize_type(dtype: str) -> str:
            """Normalize type string to DuckDB type.

            Handles PyIceberg types, Python types, and plain strings.

            Args:
                dtype: Type string to normalize.

            Returns:
                Normalized DuckDB type string.

            """
            dtype_str = str(dtype).lower()

            # Map PyIceberg/Pandera types to DuckDB types
            type_mapping = {
                "int32": "INTEGER",
                "int64": "BIGINT",
                "int": "INTEGER",
                "long": "BIGINT",
                "float": "FLOAT",
                "double": "DOUBLE",
                "string": "VARCHAR",
                "str": "VARCHAR",
                "bool": "BOOLEAN",
                "boolean": "BOOLEAN",
                "date": "DATE",
                "timestamp": "TIMESTAMP",
                "datetime": "TIMESTAMP",
                "object": "VARCHAR",
                "bytes": "BLOB",
            }

            for key, val in type_mapping.items():
                if key in dtype_str:
                    return val

            # Default to VARCHAR for unknown types
            return "VARCHAR"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dtype&#x22;" type="&#x22;str&#x22;" value="undefined">
          Type string to normalize.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Normalized DuckDB type string.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
