# observatory_plugin (/docs/python-reference/packages/phlo-lineage/phlo_lineage/observatory_plugin)



Observatory extension plugin for lineage graph UI.

This module provides the LineageObservatoryExtension class, which integrates
the phlo-lineage visualization features into the Observatory web UI. It registers
the lineage graph view as a navigation item and serves static assets.

Extension Features:

* Lineage Graph navigation item in Observatory UI
* Static assets for lineage visualization (JS, CSS, images)
* Compatibility checking with Observatory core version

Plugin Registration:
This extension is auto-discovered via entry points. The Observatory framework
loads and initializes it automatically.

Asset Structure:
Static assets are bundled in the package at:
phlo\_lineage/observatory\_assets/

Example:
Once loaded, users can navigate to /graph in Observatory to view:

* Interactive lineage graph visualization
* Asset dependency relationships
* Column-level lineage details

See Also:
phlo.plugins.observatory for the extension plugin interface.
phlo\_lineage.graph for graph construction logic.

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;LineageObservatoryExtension&#x22;" href="&#x22;/docs/python-reference/packages/phlo-lineage/phlo_lineage/observatory_plugin/LineageObservatoryExtension&#x22;" />
    </Cards>
  </Tab>
</Tabs>
