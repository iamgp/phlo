# SchemaMigrator (/docs/python-reference/core/phlo/capabilities/interfaces/SchemaMigrator)



Protocol for storage-layer schema migration providers.

Each storage provider (Iceberg, Delta, Hudi) implements this protocol
and determines its own classification rules based on its capabilities.

Functions [#functions]

<PyFunction name="&#x22;supported_changes&#x22;" type="&#x22;(self) -> set[str]&#x22;">
  Return the set of change\_type values this provider supports natively.

  <PySourceCode>
    ```python
    def supported_changes(self) -> set[str]:
        """Return the set of change_type values this provider supports natively."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;set[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;classify_change&#x22;" type="&#x22;(self, change_type, **details) -> str&#x22;">
  Classify a single change as 'safe', 'warning', or 'breaking'.

  <PySourceCode>
    ```python
    def classify_change(self, change_type: str, **details: Any) -> str:
        """Classify a single change as 'safe', 'warning', or 'breaking'."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;change_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;details&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;" />
</PyFunction>

<PyFunction name="&#x22;diff_schema&#x22;" type="&#x22;(self, *, table_name, desired) -> Any&#x22;">
  Compare desired schema against current table and produce a migration plan.

  <PySourceCode>
    ```python
    def diff_schema(self, *, table_name: str, desired: Any) -> Any:
        """Compare desired schema against current table and produce a migration plan."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;desired&#x22;" type="&#x22;Any&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
</PyFunction>

<PyFunction name="&#x22;apply_plan&#x22;" type="&#x22;(self, *, plan, approved=False) -> dict[str, Any]&#x22;">
  Execute a migration plan. Breaking changes require approved=True.

  <PySourceCode>
    ```python
    def apply_plan(self, *, plan: Any, approved: bool = False) -> dict[str, Any]:
        """Execute a migration plan. Breaking changes require approved=True."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plan&#x22;" type="&#x22;Any&#x22;" value="null" />

    <PyParameter name="&#x22;approved&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_schema_history&#x22;" type="&#x22;(self, *, table_name, limit=10) -> list[dict[str, Any]]&#x22;">
  Return schema version history for a table.

  <PySourceCode>
    ```python
    def get_schema_history(self, *, table_name: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return schema version history for a table."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;10&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;list[dict[str, typing.Any]]&#x22;" />
</PyFunction>
