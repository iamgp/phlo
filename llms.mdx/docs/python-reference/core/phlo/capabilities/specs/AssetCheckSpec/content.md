# AssetCheckSpec (/docs/python-reference/core/phlo/capabilities/specs/AssetCheckSpec)



Check spec for assets, with optional execution function.

Attributes [#attributes]

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;fn&#x22;" type="&#x22;Callable[[RuntimeContext], CheckResult] | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;blocking&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />

<PyAttribute name="&#x22;description&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;severity&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, name, asset_key, fn=None, blocking=True, description=None, severity=None, tags=dict()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;fn&#x22;" type="&#x22;Callable[[RuntimeContext], CheckResult] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;blocking&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />

    <PyParameter name="&#x22;description&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;severity&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
