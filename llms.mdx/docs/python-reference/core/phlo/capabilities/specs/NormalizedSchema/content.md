# NormalizedSchema (/docs/python-reference/core/phlo/capabilities/specs/NormalizedSchema)



Provider-agnostic schema representation.

Quality providers (Pandera, Great Expectations, etc.) convert their native
schemas into this form; storage providers consume it for diff/migration.

Attributes [#attributes]

<PyAttribute name="&#x22;fields&#x22;" type="&#x22;list[FieldSpec]&#x22;" value="null" />

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, fields, metadata=dict()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;fields&#x22;" type="&#x22;list[FieldSpec]&#x22;" value="null" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;dict()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
