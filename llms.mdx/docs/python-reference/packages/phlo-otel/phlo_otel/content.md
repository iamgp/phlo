# phlo_otel (/docs/python-reference/packages/phlo-otel/phlo_otel)



OpenTelemetry instrumentation for Phlo hook events.

This module provides the public API for the phlo-otel package, exposing
the core OpenTelemetry components (tracer, meter, log emitter) and lifecycle
management functions.

Example:
from phlo\_otel import get\_tracer, get\_meter

tracer = get\_tracer()
meter = get\_meter()

with tracer.start\_as\_current\_span("my\_operation") as span:
counter = meter.create\_counter("operations")
counter.add(1)

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['get_log_emitter', 'get_tracer', 'get_meter', 'shutdown_otel']&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-otel/phlo_otel/hooks_plugin&#x22;" title="&#x22;hooks_plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-otel/phlo_otel/provider&#x22;" title="&#x22;provider&#x22;" />
    </Cards>
  </Tab>
</Tabs>
