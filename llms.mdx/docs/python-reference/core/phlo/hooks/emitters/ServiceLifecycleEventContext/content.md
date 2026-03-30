# ServiceLifecycleEventContext (/docs/python-reference/core/phlo/hooks/emitters/ServiceLifecycleEventContext)



Shared context for service lifecycle event emissions.

Attributes [#attributes]

<PyAttribute name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;project_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;project_root&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;container_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="&#x22;field(default_factory=HookCorrelation)&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, service_name, project_name=None, project_root=None, container_name=None, tags=dict(), correlation=HookCorrelation()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;project_root&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;container_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="&#x22;HookCorrelation()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
