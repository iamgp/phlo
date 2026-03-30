# LogEvent (/docs/python-reference/core/phlo/hooks/events/LogEvent)



Event emitted for structured log records.

Attributes [#attributes]

<PyAttribute name="&#x22;logger&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;level&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;service&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;asset_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;job_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;check_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, *, event_type, version=EVENT_VERSION, timestamp=_utc_now(), tags=dict(), correlation=HookCorrelation(), logger, level, message, service=None, run_id=None, asset_key=None, job_name=None, partition_key=None, check_name=None, metadata=dict()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;version&#x22;" type="&#x22;str&#x22;" value="&#x22;EVENT_VERSION&#x22;" />

    <PyParameter name="&#x22;timestamp&#x22;" type="&#x22;datetime&#x22;" value="&#x22;_utc_now()&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="&#x22;HookCorrelation()&#x22;" />

    <PyParameter name="&#x22;logger&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;level&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;service&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;job_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;check_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;dict()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
