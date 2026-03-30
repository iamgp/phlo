# PublishEventContext (/docs/python-reference/core/phlo/hooks/emitters/PublishEventContext)



Shared context for publish event emissions.

Attributes [#attributes]

<PyAttribute name="&#x22;asset_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;target_system&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;tables&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="&#x22;field(default_factory=HookCorrelation)&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, asset_key=None, run_id=None, partition_key=None, target_system=None, tables=dict(), tags=dict(), correlation=HookCorrelation()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;target_system&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;tables&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="&#x22;HookCorrelation()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
