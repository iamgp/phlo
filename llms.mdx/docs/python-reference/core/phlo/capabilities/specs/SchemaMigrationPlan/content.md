# SchemaMigrationPlan (/docs/python-reference/core/phlo/capabilities/specs/SchemaMigrationPlan)



Plan describing changes to apply to a table schema.

Attributes [#attributes]

<PyAttribute name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;changes&#x22;" type="&#x22;list[SchemaChange]&#x22;" value="null" />

<PyAttribute name="&#x22;classification&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;recommendations&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;field(default_factory=list)&#x22;" />

<PyAttribute name="&#x22;requires_approval&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, table_name, changes, classification, recommendations=list(), requires_approval=False) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;changes&#x22;" type="&#x22;list[SchemaChange]&#x22;" value="null" />

    <PyParameter name="&#x22;classification&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;recommendations&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;list()&#x22;" />

    <PyParameter name="&#x22;requires_approval&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
