# lineage_sink (/docs/python-reference/packages/phlo-lineage/phlo_lineage/lineage_sink)



Lineage sink capability provider for phlo-lineage.

This module implements the PhloLineageSink class, which wraps the low-level
LineageStore and graph functionality into a standardized capability interface.
It provides a simplified API for recording lineage events and querying lineage
information through the Phlo capability system.

The lineage sink enables:

* Asset edge recording (source -> target dependencies)
* Row-level lineage tracking with parent relationships
* Column-level lineage mapping persistence
* Graph retrieval for visualization
* Row journey queries (ancestors and descendants)

Architecture:
PhloLineageSink is exposed as a capability provider through the plugin
system (see resource\_provider.py). It wraps LineageStore for persistence
and LineageGraph for in-memory analysis.

Example:

> > > from phlo\_lineage.lineage\_sink import PhloLineageSink
> > > sink = PhloLineageSink()
> > >
> > > Record asset dependencies [#record-asset-dependencies]
> > >
> > > sink.record\_asset\_edges(\[
> > > ...     ("bronze.orders", "silver.stg\_orders"),
> > > ...     ("silver.stg\_orders", "gold.fct\_orders"),
> > > ... ])
> > >
> > > Get the current graph [#get-the-current-graph]
> > >
> > > graph = sink.get\_asset\_graph()
> > > print(f"Total assets: \{len(graph.assets)}")

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PhloLineageSink&#x22;" href="&#x22;/docs/python-reference/packages/phlo-lineage/phlo_lineage/lineage_sink/PhloLineageSink&#x22;" />
    </Cards>
  </Tab>
</Tabs>
