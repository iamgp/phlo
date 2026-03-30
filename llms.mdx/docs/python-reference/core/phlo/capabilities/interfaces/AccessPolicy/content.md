# AccessPolicy (/docs/python-reference/core/phlo/capabilities/interfaces/AccessPolicy)



Value object describing an access control policy.

Attributes [#attributes]

<PyAttribute name="&#x22;__slots__&#x22;" type="null" value="&#x22;('policy_id', 'principal', 'table_pattern', 'action', 'effect', 'columns', 'row_filter', 'data_masking')&#x22;" />

<PyAttribute name="&#x22;policy_id&#x22;" type="null" value="&#x22;policy_id&#x22;" />

<PyAttribute name="&#x22;principal&#x22;" type="null" value="&#x22;principal&#x22;" />

<PyAttribute name="&#x22;table_pattern&#x22;" type="null" value="&#x22;table_pattern&#x22;" />

<PyAttribute name="&#x22;action&#x22;" type="null" value="&#x22;action&#x22;" />

<PyAttribute name="&#x22;effect&#x22;" type="null" value="&#x22;effect&#x22;" />

<PyAttribute name="&#x22;columns&#x22;" type="null" value="&#x22;columns&#x22;" />

<PyAttribute name="&#x22;row_filter&#x22;" type="null" value="&#x22;row_filter&#x22;" />

<PyAttribute name="&#x22;data_masking&#x22;" type="null" value="&#x22;data_masking&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, *, policy_id=None, principal, table_pattern, action='SELECT', effect='ALLOW', columns=None, row_filter=None, data_masking=None) -> None&#x22;">
  <PySourceCode>
    ```python
    def __init__(
        self,
        *,
        policy_id: str | None = None,
        principal: str,
        table_pattern: str,
        action: str = "SELECT",
        effect: str = "ALLOW",
        columns: list[str] | None = None,
        row_filter: str | None = None,
        data_masking: dict[str, str] | None = None,
    ) -> None:
        self.policy_id = policy_id
        self.principal = principal
        self.table_pattern = table_pattern
        self.action = action
        self.effect = effect
        self.columns = columns
        self.row_filter = row_filter
        self.data_masking = data_masking
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;policy_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;principal&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;table_pattern&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="&#x22;'SELECT'&#x22;" />

    <PyParameter name="&#x22;effect&#x22;" type="&#x22;str&#x22;" value="&#x22;'ALLOW'&#x22;" />

    <PyParameter name="&#x22;columns&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;row_filter&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;data_masking&#x22;" type="&#x22;dict[str, str] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
