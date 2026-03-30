# hooks_plugin (/docs/python-reference/packages/phlo-lineage/phlo_lineage/hooks_plugin)



Hook plugin for updating the lineage graph from events.

This module implements the LineageHookPlugin class, which integrates with the
Phlo hooks system to receive lineage events and update both the in-memory graph
and persistent store. It enables real-time lineage tracking as assets are
materialized in the pipeline.

Event Handling:
The plugin subscribes to lineage\_events hook type and specifically filters
for lineage.edges events. When received, it:

1. Updates the in-memory LineageGraph (immediate visibility)
2. Persists edges to PostgreSQL LineageStore (durability)

Architecture:

* Implements HookPlugin interface for plugin system integration
* Uses lazy database connection resolution
* Gracefully handles missing database configuration (logs only)
* Failures in persistence don't affect in-memory graph updates

Performance:
In-memory graph updates are synchronous and fast (O(1) per edge).
Database persistence involves network round-trips and should be
considered in high-throughput scenarios.

Example:
The plugin is auto-discovered via entry points. No manual registration
is required. Events are emitted by the orchestration layer during
asset materialization.

See Also:
phlo.hooks for the event system.
phlo.plugins.hooks for plugin interface definitions.
phlo\_lineage.graph.get\_lineage\_graph() for the in-memory graph.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;LineageHookPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-lineage/phlo_lineage/hooks_plugin/LineageHookPlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
