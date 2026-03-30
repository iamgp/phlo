# ServicePlugin (/docs/python-reference/core/phlo/plugins/base/service/ServicePlugin)



Base class for service plugins.

Service plugins provide Docker-based infrastructure components
that can be composed into a Phlo stack.

Attributes [#attributes]

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Return the service definition.

  This is equivalent to the content of a service.yaml file.
</PyAttribute>

<PyAttribute name="&#x22;category&#x22;" type="&#x22;str&#x22;" value="null">
  Service category (core, api, bi, observability, etc.).
</PyAttribute>

<PyAttribute name="&#x22;is_default&#x22;" type="&#x22;bool&#x22;" value="null">
  Whether this service should be installed by default.
</PyAttribute>

<PyAttribute name="&#x22;profile&#x22;" type="&#x22;str | None&#x22;" value="null">
  Optional profile this service belongs to.
</PyAttribute>

<PyAttribute name="&#x22;requires_capabilities&#x22;" type="&#x22;list[str]&#x22;" value="null">
  Return required capabilities for this service plugin.
</PyAttribute>

<PyAttribute name="&#x22;optional_capabilities&#x22;" type="&#x22;list[str]&#x22;" value="null">
  Return optional capabilities for this service plugin.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_compose_fragment&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Return Docker Compose service configuration.

  <PySourceCode>
    ```python
    def get_compose_fragment(self) -> dict[str, Any]:
        """Return Docker Compose service configuration."""
        return self.service_definition.get("compose", {})
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_files&#x22;" type="&#x22;(self) -> list[dict[str, str]]&#x22;">
  Return files to copy during initialization.

  <PySourceCode>
    ```python
    def get_files(self) -> list[dict[str, str]]:
        """Return files to copy during initialization."""
        return self.service_definition.get("files", [])
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[dict[str, str]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_dependencies&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  Return list of service names this depends on.

  <PySourceCode>
    ```python
    def get_dependencies(self) -> list[str]:
        """Return list of service names this depends on."""
        return self.service_definition.get("depends_on", [])
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[str]&#x22;" />
</PyFunction>
