# exceptions (/docs/python-reference/core/phlo/exceptions)



Phlo Exception Classes

Structured error classes with error codes, contextual messages, and suggestions.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PhloErrorCode&#x22;" href="&#x22;/docs/python-reference/core/phlo/exceptions/PhloErrorCode&#x22;" />

      <Card title="&#x22;PhloError&#x22;" href="&#x22;/docs/python-reference/core/phlo/exceptions/PhloError&#x22;" />

      <Card title="&#x22;PhloDiscoveryError&#x22;" href="&#x22;/docs/python-reference/core/phlo/exceptions/PhloDiscoveryError&#x22;" />

      <Card title="&#x22;PhloSchemaError&#x22;" href="&#x22;/docs/python-reference/core/phlo/exceptions/PhloSchemaError&#x22;" />

      <Card title="&#x22;PhloCronError&#x22;" href="&#x22;/docs/python-reference/core/phlo/exceptions/PhloCronError&#x22;" />

      <Card title="&#x22;PhloValidationError&#x22;" href="&#x22;/docs/python-reference/core/phlo/exceptions/PhloValidationError&#x22;" />

      <Card title="&#x22;PhloConfigError&#x22;" href="&#x22;/docs/python-reference/core/phlo/exceptions/PhloConfigError&#x22;" />

      <Card title="&#x22;PhloIngestionError&#x22;" href="&#x22;/docs/python-reference/core/phlo/exceptions/PhloIngestionError&#x22;" />

      <Card title="&#x22;PhloTableError&#x22;" href="&#x22;/docs/python-reference/core/phlo/exceptions/PhloTableError&#x22;" />

      <Card title="&#x22;PhloInfrastructureError&#x22;" href="&#x22;/docs/python-reference/core/phlo/exceptions/PhloInfrastructureError&#x22;" />

      <Card title="&#x22;PhloCapabilitySetupError&#x22;" href="&#x22;/docs/python-reference/core/phlo/exceptions/PhloCapabilitySetupError&#x22;" />

      <Card title="&#x22;SchemaConversionError&#x22;" href="&#x22;/docs/python-reference/core/phlo/exceptions/SchemaConversionError&#x22;" />

      <Card title="&#x22;DLTPipelineError&#x22;" href="&#x22;/docs/python-reference/core/phlo/exceptions/DLTPipelineError&#x22;" />

      <Card title="&#x22;IcebergCatalogError&#x22;" href="&#x22;/docs/python-reference/core/phlo/exceptions/IcebergCatalogError&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;suggest_similar_field_names&#x22;" type="&#x22;(invalid_field, valid_fields, max_suggestions=3) -> list[str]&#x22;">
      Generate "Did you mean?" suggestions for field name typos.

      Uses fuzzy matching to suggest similar field names.

      <PySourceCode>
        ```python
        def suggest_similar_field_names(
            invalid_field: str,
            valid_fields: list[str],
            max_suggestions: int = 3,
        ) -> list[str]:
            """
            Generate "Did you mean?" suggestions for field name typos.

            Uses fuzzy matching to suggest similar field names.

            Args:
                invalid_field: The invalid field name provided by user
                valid_fields: List of valid field names from schema
                max_suggestions: Maximum number of suggestions to return

            Returns:
                List of suggested field names
            """
            from difflib import get_close_matches

            similar = get_close_matches(
                invalid_field,
                valid_fields,
                n=max_suggestions,
                cutoff=0.6,  # Similarity threshold (0-1)
            )

            if similar:
                return [f"Did you mean '{field}'?" for field in similar]
            return [f"Available fields: {', '.join(valid_fields)}"]
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;invalid_field&#x22;" type="&#x22;str&#x22;" value="undefined">
          The invalid field name provided by user
        </PyParameter>

        <PyParameter name="&#x22;valid_fields&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
          List of valid field names from schema
        </PyParameter>

        <PyParameter name="&#x22;max_suggestions&#x22;" type="&#x22;int&#x22;" value="&#x22;3&#x22;">
          Maximum number of suggestions to return
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of suggested field names
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;format_field_list&#x22;" type="&#x22;(fields) -> str&#x22;">
      Format a list of fields for error messages.

      <PySourceCode>
        ```python
        def format_field_list(fields: list[str]) -> str:
            """Format a list of fields for error messages."""
            return ", ".join(f"'{field}'" for field in fields)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;fields&#x22;" type="&#x22;list[str]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
