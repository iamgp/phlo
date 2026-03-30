# plugin (/docs/python-reference/packages/phlo-superset/phlo_superset/plugin)



Superset service plugin for Phlo.

This module provides the plugin implementation for integrating Apache Superset
as a managed service within the Phlo platform. It exposes service metadata
and Docker Compose definitions through the Phlo plugin system.

Example:

> > > from phlo\_superset.plugin import SupersetServicePlugin
> > > plugin = SupersetServicePlugin()
> > > print(plugin.metadata.name)
> > > 'superset'

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;SupersetServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-superset/phlo_superset/plugin/SupersetServicePlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
