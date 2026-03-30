# governance (/docs/python-reference/packages/phlo-trino/phlo_trino/governance)



Trino governance backend for access control via SQL grants.

This module implements the GovernanceBackend interface using Trino's
native SQL GRANT/DENY/REVOKE commands for access control management.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;TrinoGovernanceBackend&#x22;" href="&#x22;/docs/python-reference/packages/phlo-trino/phlo_trino/governance/TrinoGovernanceBackend&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_validate_identifier&#x22;" type="&#x22;(value, label) -> str&#x22;">
      Validate a SQL identifier to prevent injection.

      <PySourceCode>
        ```python
        def _validate_identifier(value: str, label: str) -> str:
            """Validate a SQL identifier to prevent injection.

            Args:
                value: Identifier string to validate.
                label: Human-readable label for error messages.

            Returns:
                The validated identifier.

            Raises:
                ValueError: If the identifier contains invalid characters.

            """
            if not _IDENTIFIER_RE.match(value):
                raise ValueError(f"Invalid {label}: {value!r}")
            return value
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;str&#x22;" value="undefined">
          Identifier string to validate.
        </PyParameter>

        <PyParameter name="&#x22;label&#x22;" type="&#x22;str&#x22;" value="undefined">
          Human-readable label for error messages.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        The validated identifier.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
