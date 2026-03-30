# RuntimeContext (/docs/python-reference/core/phlo/capabilities/runtime/RuntimeContext)



Orchestrator-agnostic runtime context.

Attributes [#attributes]

<PyAttribute name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="null" />

<PyAttribute name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="null" />

<PyAttribute name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="null" />

<PyAttribute name="&#x22;logger&#x22;" type="&#x22;Any&#x22;" value="null">
  Return the orchestrator-provided logger.
</PyAttribute>

<PyAttribute name="&#x22;resources&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Return runtime resources keyed by resource name.
</PyAttribute>

<PyAttribute name="&#x22;routing&#x22;" type="&#x22;RuntimeRouting&#x22;" value="null">
  Return canonical runtime routing information.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_resource&#x22;" type="&#x22;(self, name) -> Any&#x22;">
  Return a runtime resource by name.

  <PySourceCode>
    ```python
    def get_resource(self, name: str) -> Any:
        """Return a runtime resource by name.

        Args:
            name: Resource identifier.

        Returns:
            Any: Resource object for the provided name.
        """
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Resource identifier.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Resource object for the provided name.
  </PyFunctionReturn>
</PyFunction>
