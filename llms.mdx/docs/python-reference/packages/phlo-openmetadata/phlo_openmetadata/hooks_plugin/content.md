# hooks_plugin (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/hooks_plugin)



Hook plugin for OpenMetadata integration.

Registers hook handlers that sync lineage, quality results, and publish
events into OpenMetadata automatically during pipeline execution.

Supported hooks:

* lineage.edges: Sync lineage edges to OpenMetadata
* quality.result: Sync quality check results as test cases
* publish.end: Sync published table metadata

Example:
The plugin is auto-discovered by phlo's hook system and begins syncing
automatically when configured.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;OpenMetadataHookPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/hooks_plugin/OpenMetadataHookPlugin&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_resolve_table_fqn&#x22;" type="&#x22;(event) -> str | None&#x22;">
      Resolve the table FQN from quality event metadata.

      <PySourceCode>
        ```python
        def _resolve_table_fqn(event: QualityResultEvent) -> str | None:
            """Resolve the table FQN from quality event metadata.

            Args:
                event: QualityResultEvent to extract table information from.

            Returns:
                str | None: Fully qualified table name or None if not found.

            """
            for key in ("table_fqn", "table_name", "table"):
                value = event.metadata.get(key)
                if isinstance(value, str) and value:
                    return value
            if event.asset_key:
                return event.asset_key
            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;event&#x22;" type="&#x22;QualityResultEvent&#x22;" value="undefined">
          QualityResultEvent to extract table information from.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        str | None: Fully qualified table name or None if not found.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_resolve_test_type&#x22;" type="&#x22;(event) -> str&#x22;">
      Map quality check types to OpenMetadata test types.

      <PySourceCode>
        ```python
        def _resolve_test_type(event: QualityResultEvent) -> str:
            """Map quality check types to OpenMetadata test types.

            Args:
                event: QualityResultEvent with check type information.

            Returns:
                str: OpenMetadata test type string.

            """
            check_type = event.check_type or ""
            if check_type.lower() == "pandera":
                return "schemaCheck"
            return QualityCheckMapper.CHECK_TYPE_MAP.get(check_type, "customCheck")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;event&#x22;" type="&#x22;QualityResultEvent&#x22;" value="undefined">
          QualityResultEvent with check type information.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        OpenMetadata test type string.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_resolve_entity_type&#x22;" type="&#x22;(event) -> str&#x22;">
      Infer entity type for OpenMetadata tests.

      <PySourceCode>
        ```python
        def _resolve_entity_type(event: QualityResultEvent) -> str:
            """Infer entity type for OpenMetadata tests.

            Args:
                event: QualityResultEvent to determine entity scope from.

            Returns:
                str: 'COLUMN' for column-level checks, otherwise 'TABLE'.

            """
            check_type = (event.check_type or "").lower()
            if check_type in {"nullcheck", "rangecheck", "uniquecheck", "freshnesscheck"}:
                return "COLUMN"
            return "TABLE"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;event&#x22;" type="&#x22;QualityResultEvent&#x22;" value="undefined">
          QualityResultEvent to determine entity scope from.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        'COLUMN' for column-level checks, otherwise 'TABLE'.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_split_table_fqn&#x22;" type="&#x22;(table_fqn, default_schema) -> tuple[str, str]&#x22;">
      Split a table FQN into schema and table name components.

      <PySourceCode>
        ```python
        def _split_table_fqn(table_fqn: str, default_schema: str) -> tuple[str, str]:
            """Split a table FQN into schema and table name components.

            Args:
                table_fqn: Fully qualified table name (e.g., 'schema.table' or 'table').
                default_schema: Schema to use if FQN has no dot separator.

            Returns:
                tuple[str, str]: Tuple of (schema_name, table_name).

            """
            if "." not in table_fqn:
                return default_schema, table_fqn
            schema_name, table_name = table_fqn.split(".", 1)
            return schema_name, table_name
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
          Fully qualified table name (e.g., 'schema.table' or 'table').
        </PyParameter>

        <PyParameter name="&#x22;default_schema&#x22;" type="&#x22;str&#x22;" value="undefined">
          Schema to use if FQN has no dot separator.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;tuple&#x22;">
        tuple\[str, str]: Tuple of (schema\_name, table\_name).
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
