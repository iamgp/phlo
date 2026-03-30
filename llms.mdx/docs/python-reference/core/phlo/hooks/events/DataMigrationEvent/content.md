# DataMigrationEvent (/docs/python-reference/core/phlo/hooks/events/DataMigrationEvent)



Event emitted for data migration lifecycle stages.

Attributes [#attributes]

<PyAttribute name="&#x22;migration_name&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;source_type&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;destination_table&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;rows_read&#x22;" type="&#x22;int&#x22;" value="null" />

<PyAttribute name="&#x22;rows_written&#x22;" type="&#x22;int&#x22;" value="null" />

<PyAttribute name="&#x22;chunk_index&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;metrics&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, *, event_type, version=EVENT_VERSION, timestamp=_utc_now(), tags=dict(), correlation=HookCorrelation(), migration_name, source_type, destination_table, status, rows_read, rows_written, chunk_index=None, metrics=dict()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;version&#x22;" type="&#x22;str&#x22;" value="&#x22;EVENT_VERSION&#x22;" />

    <PyParameter name="&#x22;timestamp&#x22;" type="&#x22;datetime&#x22;" value="&#x22;_utc_now()&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="&#x22;HookCorrelation()&#x22;" />

    <PyParameter name="&#x22;migration_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;source_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;destination_table&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;rows_read&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;rows_written&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;chunk_index&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;metrics&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;dict()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
