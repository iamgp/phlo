# resource (/docs/python-reference/packages/phlo-delta/phlo_delta/resource)



Delta Lake resource wrapper for Phlo table store interface.

This module provides the DeltaResource class that wraps Delta Lake table
operations and integrates with the Phlo resource provider system. It handles
table lifecycle operations, data ingestion, and maintenance operations.

Example:
from phlo\_delta.resource import DeltaResource

resource = DeltaResource()
table = resource.get\_table("raw\.events")
resource.append\_parquet("raw\.events", "/data/events.parquet")

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DeltaResource&#x22;" href="&#x22;/docs/python-reference/packages/phlo-delta/phlo_delta/resource/DeltaResource&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_load_delta_table&#x22;" type="&#x22;() -> type[Any]&#x22;">
      Load the optional DeltaTable runtime only when needed.

      Lazily imports the DeltaTable class from the deltalake package
      to avoid import-time dependencies.

      <PySourceCode>
        ```python
        def _load_delta_table() -> type[Any]:
            """Load the optional DeltaTable runtime only when needed.

            Lazily imports the DeltaTable class from the deltalake package
            to avoid import-time dependencies.

            Returns:
                type[Any]: The DeltaTable class.

            """
            return cast(Any, importlib.import_module("deltalake")).DeltaTable
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;type&#x22;">
        type\[Any]: The DeltaTable class.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_resolve_delta_ref&#x22;" type="&#x22;(override_ref) -> None&#x22;">
      Validate the requested override ref for Delta operations.

      Delta tables in Phlo are not branch-aware. Accept the default `main` ref
      for table-store interface compatibility and reject any branch-like override.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        \_resolve\_delta\_ref(None)  # OK
        \_resolve\_delta\_ref("main")  # OK
        \_resolve\_delta\_ref("dev")  # Raises PhloConfigError
      </Callout>

      <PySourceCode>
        ```python
        def _resolve_delta_ref(override_ref: str | None) -> None:
            """Validate the requested override ref for Delta operations.

            Delta tables in Phlo are not branch-aware. Accept the default ``main`` ref
            for table-store interface compatibility and reject any branch-like override.

            Args:
                override_ref: Optional branch reference to validate.

            Raises:
                PhloConfigError: If an unsupported override_ref is provided.

            Example:
                _resolve_delta_ref(None)  # OK
                _resolve_delta_ref("main")  # OK
                _resolve_delta_ref("dev")  # Raises PhloConfigError

            """
            if override_ref in (None, "", "main"):
                return
            raise PhloConfigError(
                message=f"Delta table_store does not support override_ref={override_ref!r}",
                suggestions=[
                    "Use the default main ref when writing to Delta tables",
                    "Use phlo-iceberg if you need Nessie branch-aware table writes",
                ],
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Optional branch reference to validate.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_partition_columns_from_spec&#x22;" type="&#x22;(partition_spec) -> list[str] | None&#x22;">
      Convert shared partition\_spec tuples into Delta partition columns.

      Delta Lake only supports identity partitioning here, so transforms such as
      `day` or `bucket` must be rejected explicitly.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        cols = \_partition\_columns\_from\_spec(\[("date", "identity")])

        Returns: ["date"] [#returns-date]
      </Callout>

      <PySourceCode>
        ```python
        def _partition_columns_from_spec(
            partition_spec: Sequence[tuple[str, str] | str] | None,
        ) -> list[str] | None:
            """Convert shared partition_spec tuples into Delta partition columns.

            Delta Lake only supports identity partitioning here, so transforms such as
            ``day`` or ``bucket`` must be rejected explicitly.

            Args:
                partition_spec: Partition specification, either as column names or
                    (column, transform) tuples.

            Returns:
                list[str] | None: List of partition column names, or None if no partitioning.

            Raises:
                PhloConfigError: If invalid partition spec format or unsupported transforms.

            Example:
                cols = _partition_columns_from_spec([("date", "identity")])
                # Returns: ["date"]

            """
            if not partition_spec:
                return None

            partition_columns: list[str] = []
            for entry in partition_spec:
                if isinstance(entry, str):
                    partition_columns.append(entry)
                    continue

                if not isinstance(entry, (tuple, list)) or len(entry) != 2:
                    raise PhloConfigError(
                        message="Delta partition_spec entries must be column names or (column, transform) pairs",
                        suggestions=[
                            "Use partition_spec=[('column', 'identity')] for Delta tables",
                            "Or omit partition_spec entirely for unpartitioned Delta tables",
                        ],
                    )

                source_name, transform_name = entry
                if not isinstance(source_name, str) or not isinstance(transform_name, str):
                    raise PhloConfigError(
                        message="Delta partition_spec entries must contain string column and transform names",
                        suggestions=[
                            "Use partition_spec=[('column', 'identity')] for Delta tables",
                        ],
                    )
                if transform_name != "identity":
                    raise PhloConfigError(
                        message=f"Delta table_store only supports identity partition transforms, got {transform_name!r}",
                        suggestions=[
                            "Use partition_spec=[('column', 'identity')] with Delta",
                            "Use phlo-iceberg for transform-based partitioning like day/month/bucket",
                        ],
                    )
                partition_columns.append(source_name)

            return partition_columns
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;partition_spec&#x22;" type="&#x22;Sequence[tuple[str, str] | str] | None&#x22;" value="undefined">
          Partition specification, either as column names or
          (column, transform) tuples.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[str] | None&#x22;">
        list\[str] | None: List of partition column names, or None if no partitioning.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
