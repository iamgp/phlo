# GovernancePlugin (/docs/python-reference/core/phlo/plugins/base/governance/GovernancePlugin)



Base class for governance plugins.

Governance plugins provide access control, data masking, row-level
security, and policy enforcement for lakehouse tables.

Example:

```python
class TrinoRBACPlugin(GovernancePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="trino-rbac",
            version="1.0.0",
            description="Trino RBAC governance",
        )

    def list_policies(self, table_name=None):
        return self._fetch_policies(table_name)

    def apply_policy(self, policy):
        self._execute_grant(policy)

    def revoke_policy(self, policy_id):
        self._execute_revoke(policy_id)

    def check_access(self, principal, table_name, action):
        return self._query_access(principal, table_name, action)
```

Functions [#functions]

<PyFunction name="&#x22;list_policies&#x22;" type="&#x22;(self, *, table_name=None) -> list[dict[str, Any]]&#x22;">
  List access policies, optionally filtered by table.

  <PySourceCode>
    ```python
    @abstractmethod
    def list_policies(self, *, table_name: str | None = None) -> list[dict[str, Any]]:
        """List access policies, optionally filtered by table."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;list[dict[str, typing.Any]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;apply_policy&#x22;" type="&#x22;(self, *, policy) -> None&#x22;">
  Apply an access policy.

  <PySourceCode>
    ```python
    @abstractmethod
    def apply_policy(self, *, policy: AccessPolicy) -> None:
        """Apply an access policy."""
        raise NotImplementedError
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
    @abstractmethod
    def revoke_policy(self, *, policy_id: str) -> None:
        """Revoke an access policy by identifier."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;policy_id&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;check_access&#x22;" type="&#x22;(self, *, principal, table_name, action) -> bool&#x22;">
  Check whether a principal has access. Returns True by default.

  <PySourceCode>
    ```python
    def check_access(self, *, principal: str, table_name: str, action: str) -> bool:
        """Check whether a principal has access. Returns True by default."""
        return True
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

<PyFunction name="&#x22;get_masking_rules&#x22;" type="&#x22;(self, *, table_name) -> list[dict[str, Any]]&#x22;">
  Return column masking rules for a table.

  <PySourceCode>
    ```python
    def get_masking_rules(self, *, table_name: str) -> list[dict[str, Any]]:
        """Return column masking rules for a table."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[dict[str, typing.Any]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_row_filters&#x22;" type="&#x22;(self, *, table_name) -> list[dict[str, Any]]&#x22;">
  Return row-level filter rules for a table.

  <PySourceCode>
    ```python
    def get_row_filters(self, *, table_name: str) -> list[dict[str, Any]]:
        """Return row-level filter rules for a table."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[dict[str, typing.Any]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_data_classifications&#x22;" type="&#x22;(self) -> Iterable[dict[str, Any]]&#x22;">
  Return data classification tags (PII, sensitive, public, etc.).

  <PySourceCode>
    ```python
    def get_data_classifications(self) -> Iterable[dict[str, Any]]:
        """Return data classification tags (PII, sensitive, public, etc.)."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[dict[str, typing.Any]]&#x22;" />
</PyFunction>
