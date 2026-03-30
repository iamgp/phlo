# HookEvent (/docs/python-reference/core/phlo/hooks/events/HookEvent)



Base event payload shared by all hook events.

This is the foundational event class that all other event types inherit from.
It provides the common structure for event routing, versioning, and
correlation tracking.

Attributes [#attributes]

<PyAttribute name="&#x22;event_type&#x22;" type="&#x22;str&#x22;" value="null">
  Event type identifier used for routing (e.g., "ingestion.start").
</PyAttribute>

<PyAttribute name="&#x22;version&#x22;" type="&#x22;str&#x22;" value="&#x22;EVENT_VERSION&#x22;">
  Event schema version for forward/backward compatibility.
</PyAttribute>

<PyAttribute name="&#x22;timestamp&#x22;" type="&#x22;datetime&#x22;" value="&#x22;field(default_factory=_utc_now)&#x22;">
  UTC timestamp when the event was created.
</PyAttribute>

<PyAttribute name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;field(default_factory=dict)&#x22;">
  Optional key-value tags for event categorization and filtering.
</PyAttribute>

<PyAttribute name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="&#x22;field(default_factory=HookCorrelation)&#x22;">
  Correlation context for distributed tracing and observability.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, *, event_type, version=EVENT_VERSION, timestamp=_utc_now(), tags=dict(), correlation=HookCorrelation()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;version&#x22;" type="&#x22;str&#x22;" value="&#x22;EVENT_VERSION&#x22;" />

    <PyParameter name="&#x22;timestamp&#x22;" type="&#x22;datetime&#x22;" value="&#x22;_utc_now()&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="&#x22;HookCorrelation()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
