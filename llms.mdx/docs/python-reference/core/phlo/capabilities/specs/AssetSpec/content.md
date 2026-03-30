# AssetSpec (/docs/python-reference/core/phlo/capabilities/specs/AssetSpec)



Orchestrator-agnostic asset specification.

Attributes [#attributes]

<PyAttribute name="&#x22;key&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;group&#x22;" type="&#x22;str | None&#x22;" value="null" />

<PyAttribute name="&#x22;description&#x22;" type="&#x22;str | None&#x22;" value="null" />

<PyAttribute name="&#x22;kinds&#x22;" type="&#x22;set[str]&#x22;" value="&#x22;field(default_factory=set)&#x22;" />

<PyAttribute name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;capability_overrides&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;partitions&#x22;" type="&#x22;PartitionSpec | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;deps&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;field(default_factory=list)&#x22;" />

<PyAttribute name="&#x22;resources&#x22;" type="&#x22;set[str]&#x22;" value="&#x22;field(default_factory=set)&#x22;" />

<PyAttribute name="&#x22;run&#x22;" type="&#x22;RunSpec | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;checks&#x22;" type="&#x22;list[AssetCheckSpec]&#x22;" value="&#x22;field(default_factory=list)&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, key, group, description, kinds=set(), tags=dict(), metadata=dict(), capability_overrides=dict(), partitions=None, deps=list(), resources=set(), run=None, checks=list()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;key&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;group&#x22;" type="&#x22;str | None&#x22;" value="null" />

    <PyParameter name="&#x22;description&#x22;" type="&#x22;str | None&#x22;" value="null" />

    <PyParameter name="&#x22;kinds&#x22;" type="&#x22;set[str]&#x22;" value="&#x22;set()&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;capability_overrides&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;partitions&#x22;" type="&#x22;PartitionSpec | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;deps&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;list()&#x22;" />

    <PyParameter name="&#x22;resources&#x22;" type="&#x22;set[str]&#x22;" value="&#x22;set()&#x22;" />

    <PyParameter name="&#x22;run&#x22;" type="&#x22;RunSpec | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;checks&#x22;" type="&#x22;list[AssetCheckSpec]&#x22;" value="&#x22;list()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
