# graph (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/graph)



In-memory lineage graph used by OpenMetadata extraction flows.

Provides a simple directed graph implementation for tracking data lineage
between assets. Supports export to JSON, DOT (Graphviz), and Mermaid formats.

Example:

> > > from phlo\_openmetadata.graph import OpenMetadataLineageGraph
> > > graph = OpenMetadataLineageGraph()
> > > graph.add\_edge("source\_table", "transformed\_table")
> > > print(graph.to\_mermaid())

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;Asset&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/graph/Asset&#x22;" />

      <Card title="&#x22;OpenMetadataLineageGraph&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/graph/OpenMetadataLineageGraph&#x22;" />
    </Cards>
  </Tab>
</Tabs>
