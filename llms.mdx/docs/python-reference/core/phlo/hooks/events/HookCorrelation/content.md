# HookCorrelation (/docs/python-reference/core/phlo/hooks/events/HookCorrelation)



Shared correlation fields for cross-signal observability.

Correlation fields enable distributed tracing and request tracking across
multiple events and services. These fields are propagated through the
event chain to maintain observability context.

Attributes [#attributes]

<PyAttribute name="&#x22;request_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Unique identifier for the originating request.
</PyAttribute>

<PyAttribute name="&#x22;trace_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  OpenTelemetry trace identifier for distributed tracing.
</PyAttribute>

<PyAttribute name="&#x22;span_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  OpenTelemetry span identifier within the trace.
</PyAttribute>

<PyAttribute name="&#x22;trace_flags&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  OpenTelemetry trace flags (sampling decisions).
</PyAttribute>

<PyAttribute name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Dagster run identifier for pipeline runs.
</PyAttribute>

<PyAttribute name="&#x22;asset_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Dagster asset key for asset materializations.
</PyAttribute>

<PyAttribute name="&#x22;job_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Dagster job name for pipeline definitions.
</PyAttribute>

<PyAttribute name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Dagster partition key for partitioned runs.
</PyAttribute>

<PyAttribute name="&#x22;check_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Quality check name for quality events.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, *, request_id=None, trace_id=None, span_id=None, trace_flags=None, run_id=None, asset_key=None, job_name=None, partition_key=None, check_name=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;request_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;trace_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;span_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;trace_flags&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;job_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;check_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
