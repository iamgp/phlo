# resource_provider (/docs/python-reference/packages/phlo-lineage/phlo_lineage/resource_provider)



Resource provider plugin for phlo-lineage capabilities.

This module provides the LineageResourceProvider class, which exposes phlo-lineage
capabilities through the Phlo plugin system. It enables other Phlo components to
discover and use lineage tracking functionality as a capability provider.

Capabilities Exposed:

* LineageSinkSpec: The phlo-lineage sink for recording and querying lineage data.

Plugin Registration:
This provider is auto-discovered via entry points. No manual registration required.

Example:
The lineage sink is accessible through Phlo's capability system:

> > > from phlo.capabilities import get\_lineage\_sink
> > > sink = get\_lineage\_sink("phlo-lineage")
> > > sink.record\_asset\_edges(\[("bronze.orders", "silver.stg\_orders")])

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;LineageResourceProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-lineage/phlo_lineage/resource_provider/LineageResourceProvider&#x22;" />
    </Cards>
  </Tab>
</Tabs>
