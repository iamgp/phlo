# DataMigrationEventContext (/docs/python-reference/core/phlo/hooks/emitters/DataMigrationEventContext)



Shared context for data migration event emissions.

Attributes [#attributes]

<PyAttribute name="&#x22;migration_name&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;source_type&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;destination_table&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="&#x22;field(default_factory=HookCorrelation)&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, migration_name, source_type, destination_table, run_id=None, tags=dict(), correlation=HookCorrelation()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;migration_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;source_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;destination_table&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="&#x22;HookCorrelation()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
