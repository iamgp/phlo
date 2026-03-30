# QueryEngine (/docs/python-reference/core/phlo/capabilities/interfaces/QueryEngine)



Protocol for SQL query engines used by maintenance and discovery flows.

Functions [#functions]

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, sql, params=None, schema=None) -> Any&#x22;">
  Execute SQL and return provider-native results.

  <PySourceCode>
    ```python
    def execute(
        self,
        sql: str,
        params: Any = None,
        schema: str | None = None,
    ) -> Any:
        """Execute SQL and return provider-native results."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;sql&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;params&#x22;" type="&#x22;Any&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
</PyFunction>
