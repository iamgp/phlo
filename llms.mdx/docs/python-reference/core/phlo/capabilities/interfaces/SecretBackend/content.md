# SecretBackend (/docs/python-reference/core/phlo/capabilities/interfaces/SecretBackend)



Protocol for pluggable secret storage providers.

Functions [#functions]

<PyFunction name="&#x22;get_secret&#x22;" type="&#x22;(self, key) -> str | None&#x22;">
  Retrieve a secret value by key.

  <PySourceCode>
    ```python
    def get_secret(self, key: str) -> str | None:
        """Retrieve a secret value by key."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;key&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_secrets&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List available secret keys.

  <PySourceCode>
    ```python
    def list_secrets(self) -> list[str]:
        """List available secret keys."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[str]&#x22;" />
</PyFunction>
