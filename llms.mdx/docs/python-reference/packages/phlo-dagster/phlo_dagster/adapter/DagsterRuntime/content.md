# DagsterRuntime (/docs/python-reference/packages/phlo-dagster/phlo_dagster/adapter/DagsterRuntime)



Runtime context wrapper around `dagster.AssetExecutionContext`.

Attributes [#attributes]

<PyAttribute name="&#x22;context&#x22;" type="&#x22;dg.AssetExecutionContext&#x22;" value="null" />

<PyAttribute name="&#x22;asset_capability_overrides&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="null">
  Return the current Dagster run identifier when available.
</PyAttribute>

<PyAttribute name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="null">
  Return the active partition key for partitioned runs.
</PyAttribute>

<PyAttribute name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="null">
  Return run tags from the best available context attribute.
</PyAttribute>

<PyAttribute name="&#x22;logger&#x22;" type="&#x22;Any&#x22;" value="null">
  Expose Dagster logger for capability runtime hooks.
</PyAttribute>

<PyAttribute name="&#x22;resources&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Return resources as a plain mapping for runtime consumers.
</PyAttribute>

<PyAttribute name="&#x22;routing&#x22;" type="&#x22;RuntimeRouting&#x22;" value="null">
  Return canonical runtime routing information.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_resource&#x22;" type="&#x22;(self, name) -> Any&#x22;">
  Return a named Dagster resource from execution context.

  <PySourceCode>
    ```python
    def get_resource(self, name: str) -> Any:
        """Return a named Dagster resource from execution context.

        Args:
            name: Resource name.

        Returns:
            Resolved resource object.

        """
        return getattr(self.context.resources, name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Resource name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Resolved resource object.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, context, asset_capability_overrides=dict()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;dg.AssetExecutionContext&#x22;" value="null" />

    <PyParameter name="&#x22;asset_capability_overrides&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
