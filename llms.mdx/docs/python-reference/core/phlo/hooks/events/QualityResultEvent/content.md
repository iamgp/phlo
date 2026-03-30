# QualityResultEvent (/docs/python-reference/core/phlo/hooks/events/QualityResultEvent)



Event emitted with data quality check outcomes.

These events report the results of data quality validation checks,
including pass/fail status, severity level, and metadata about the check.

Attributes [#attributes]

<PyAttribute name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="null">
  Dagster asset key for the checked dataset.
</PyAttribute>

<PyAttribute name="&#x22;check_name&#x22;" type="&#x22;str&#x22;" value="null">
  Name of the quality check that was executed.
</PyAttribute>

<PyAttribute name="&#x22;passed&#x22;" type="&#x22;bool&#x22;" value="null">
  Boolean indicating if the check passed (True) or failed (False).
</PyAttribute>

<PyAttribute name="&#x22;severity&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Severity level if check failed ("warning", "error", "critical").
</PyAttribute>

<PyAttribute name="&#x22;check_type&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Type of quality check ("null", "range", "unique", etc.).
</PyAttribute>

<PyAttribute name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Optional partition identifier for partitioned checks.
</PyAttribute>

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;field(default_factory=dict)&#x22;">
  Additional check-specific results and context.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, *, event_type, version=EVENT_VERSION, timestamp=_utc_now(), tags=dict(), correlation=HookCorrelation(), asset_key, check_name, passed, severity=None, check_type=None, partition_key=None, metadata=dict()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;version&#x22;" type="&#x22;str&#x22;" value="&#x22;EVENT_VERSION&#x22;" />

    <PyParameter name="&#x22;timestamp&#x22;" type="&#x22;datetime&#x22;" value="&#x22;_utc_now()&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="&#x22;HookCorrelation()&#x22;" />

    <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;check_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;passed&#x22;" type="&#x22;bool&#x22;" value="null" />

    <PyParameter name="&#x22;severity&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;check_type&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;dict()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
