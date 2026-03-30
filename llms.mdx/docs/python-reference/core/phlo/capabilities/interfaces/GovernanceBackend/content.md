# GovernanceBackend (/docs/python-reference/core/phlo/capabilities/interfaces/GovernanceBackend)



Protocol for governance providers (access control, masking, policies).

Functions [#functions]

<PyFunction name="&#x22;list_policies&#x22;" type="&#x22;(self, *, table_name=None) -> list[dict[str, Any]]&#x22;">
  List access policies, optionally filtered by table.

  <PySourceCode>
    ```python
    def list_policies(self, *, table_name: str | None = None) -> list[dict[str, Any]]:
        """List access policies, optionally filtered by table."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;list[dict[str, typing.Any]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;apply_policy&#x22;" type="&#x22;(self, *, policy) -> None&#x22;">
  Apply an access policy to the backend.

  <PySourceCode>
    ```python
    def apply_policy(self, *, policy: AccessPolicy) -> None:
        """Apply an access policy to the backend."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;policy&#x22;" type="&#x22;AccessPolicy&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;revoke_policy&#x22;" type="&#x22;(self, *, policy_id) -> None&#x22;">
  Revoke an access policy by identifier.

  <PySourceCode>
    ```python
    def revoke_policy(self, *, policy_id: str) -> None:
        """Revoke an access policy by identifier."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;policy_id&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;check_access&#x22;" type="&#x22;(self, *, principal, table_name, action) -> bool&#x22;">
  Check whether a principal has access for an action on a table.

  <PySourceCode>
    ```python
    def check_access(self, *, principal: str, table_name: str, action: str) -> bool:
        """Check whether a principal has access for an action on a table."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;principal&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>
