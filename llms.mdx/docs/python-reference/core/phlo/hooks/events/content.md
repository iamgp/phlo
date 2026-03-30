# events (/docs/python-reference/core/phlo/hooks/events)



Hook event payload definitions for the Phlo plugin system.

This module defines the dataclass-based event payloads used throughout the
hook system. Each event type inherits from :class:`HookEvent` and adds
specific fields relevant to its lifecycle stage.

Event payloads are immutable dataclasses with correlation tracking for
observability and debugging. All events include:

* Event type identifier
* Version for schema evolution
* UTC timestamp
* Optional tags for categorization
* Correlation fields for distributed tracing

Key Event Types:

* :class:`IngestionEvent`: Data ingestion lifecycle
* :class:`TransformEvent`: dbt transformation lifecycle
* :class:`QualityResultEvent`: Data quality check results
* :class:`ServiceLifecycleEvent`: Service start/stop events
* :class:`SchemaMigrationEvent`: Schema change tracking
* :class:`DataMigrationEvent`: Data migration tracking
* :class:`LineageEvent`: Asset lineage tracking
* :class:`PublishEvent`: Data publication events
* :class:`TelemetryEvent`: Metrics and logging events
* :class:`LogEvent`: Structured log records

Example:

```python
from phlo.hooks.events import IngestionEvent, HookCorrelation
from datetime import UTC, datetime

event = IngestionEvent(
    event_type="ingestion.start",
    asset_key="users.raw",
    table_name="users",
    group_name="raw_data",
    correlation=HookCorrelation(
        trace_id="abc-123",
        run_id="run-456"
    )
)
```

<PyAttribute name="&#x22;EVENT_VERSION&#x22;" type="null" value="&#x22;'1.0'&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;HookCorrelation&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/events/HookCorrelation&#x22;" />

      <Card title="&#x22;HookEvent&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/events/HookEvent&#x22;" />

      <Card title="&#x22;ServiceLifecycleEvent&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/events/ServiceLifecycleEvent&#x22;" />

      <Card title="&#x22;IngestionEvent&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/events/IngestionEvent&#x22;" />

      <Card title="&#x22;TransformEvent&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/events/TransformEvent&#x22;" />

      <Card title="&#x22;PublishEvent&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/events/PublishEvent&#x22;" />

      <Card title="&#x22;QualityResultEvent&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/events/QualityResultEvent&#x22;" />

      <Card title="&#x22;LineageEvent&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/events/LineageEvent&#x22;" />

      <Card title="&#x22;TelemetryEvent&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/events/TelemetryEvent&#x22;" />

      <Card title="&#x22;SchemaMigrationEvent&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/events/SchemaMigrationEvent&#x22;" />

      <Card title="&#x22;DataMigrationEvent&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/events/DataMigrationEvent&#x22;" />

      <Card title="&#x22;LogEvent&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/events/LogEvent&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_utc_now&#x22;" type="&#x22;() -> datetime&#x22;">
      Return the current UTC timestamp.

      <PySourceCode>
        ```python
        def _utc_now() -> datetime:
            """Return the current UTC timestamp.

            Returns:
                datetime: Current time in UTC timezone.

            """
            return datetime.now(UTC)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;datetime.datetime&#x22;">
        Current time in UTC timezone.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
