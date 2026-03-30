# SchemaMigrationEvent (/docs/python-reference/core/phlo/hooks/events/SchemaMigrationEvent)



Event emitted for schema migration lifecycle stages.

Attributes [#attributes]

<PyAttribute name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;classification&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;change_count&#x22;" type="&#x22;int&#x22;" value="null" />

<PyAttribute name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;changes&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="&#x22;field(default_factory=list)&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, *, event_type, version=EVENT_VERSION, timestamp=_utc_now(), tags=dict(), correlation=HookCorrelation(), table_name, classification, change_count, status, changes=list()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;version&#x22;" type="&#x22;str&#x22;" value="&#x22;EVENT_VERSION&#x22;" />

    <PyParameter name="&#x22;timestamp&#x22;" type="&#x22;datetime&#x22;" value="&#x22;_utc_now()&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="&#x22;HookCorrelation()&#x22;" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;classification&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;change_count&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;changes&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="&#x22;list()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
