# hooks_plugin (/docs/python-reference/packages/phlo-otel/phlo_otel/hooks_plugin)



Hook plugin that translates Phlo events into OTel spans and metrics.

This module implements the OtelHookPlugin, which integrates Phlo's hook system
with OpenTelemetry. It translates various Phlo events (ingestion, transforms,
quality checks, lineage, etc.) into OTel spans and metrics for comprehensive
observability across the data platform.

The plugin handles event correlation, trace context propagation, and metric
collection, ensuring distributed traces can follow data pipelines across
multiple services and operations.

Example:
The plugin is automatically discovered and loaded by Phlo's plugin system:

from phlo.plugins.hooks import HookPlugin

Events are emitted via Phlo's hook bus and automatically translated: [#events-are-emitted-via-phlos-hook-bus-and-automatically-translated]

bus.emit(IngestionEvent(...))  # Creates OTel span + metrics

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;OtelHookPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-otel/phlo_otel/hooks_plugin/OtelHookPlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
