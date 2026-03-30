# TableConfig (/docs/python-reference/packages/phlo-dlt/phlo_dlt/registry/TableConfig)



Configuration describing a registered ingestion table.

Immutable dataclass that stores all configuration needed for a DLT
ingestion table, including name, schemas, keys, and partitioning.

Attributes [#attributes]

<PyAttribute name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null">
  Physical target table name (without namespace).
</PyAttribute>

<PyAttribute name="&#x22;table_schema&#x22;" type="&#x22;Any | None&#x22;" value="null">
  Optional explicit table-store schema object.
  If None, will be derived from validation\_schema.
</PyAttribute>

<PyAttribute name="&#x22;validation_schema&#x22;" type="&#x22;type[DataFrameModel] | None&#x22;" value="null">
  Optional Pandera DataFrameModel used for validation.
</PyAttribute>

<PyAttribute name="&#x22;unique_key&#x22;" type="&#x22;str&#x22;" value="null">
  Column used as unique key for merge semantics.
</PyAttribute>

<PyAttribute name="&#x22;group_name&#x22;" type="&#x22;str&#x22;" value="null">
  Dagster group name for generated assets.
</PyAttribute>

<PyAttribute name="&#x22;partition_spec&#x22;" type="&#x22;list[tuple[str, str]] | None&#x22;" value="&#x22;None&#x22;">
  Optional table-store partition transform specification.
  Format: list of (column, transform) tuples, e.g., \[("date", "day")]
</PyAttribute>

<PyAttribute name="&#x22;full_table_name&#x22;" type="&#x22;str&#x22;" value="null">
  Return fully qualified table name with default namespace.

  Combines the configured default namespace with the table name
  to create a fully-qualified identifier for the table store.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    config = TableConfig(
        table_name="events",
        table_schema=None,
        validation_schema=None,
        unique_key="id",
        group_name="raw",
    )
    print(config.full_table_name)  # "raw.events"
    ```
  </Callout>
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, table_name, table_schema, validation_schema, unique_key, group_name, partition_spec=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;table_schema&#x22;" type="&#x22;Any | None&#x22;" value="null" />

    <PyParameter name="&#x22;validation_schema&#x22;" type="&#x22;type[DataFrameModel] | None&#x22;" value="null" />

    <PyParameter name="&#x22;unique_key&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;group_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;partition_spec&#x22;" type="&#x22;list[tuple[str, str]] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
