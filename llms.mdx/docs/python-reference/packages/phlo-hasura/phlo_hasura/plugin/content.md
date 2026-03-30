# plugin (/docs/python-reference/packages/phlo-hasura/phlo_hasura/plugin)



Hasura service plugin.

This module provides the HasuraServicePlugin class that integrates Hasura
with the Phlo plugin system. It exposes service metadata and Docker service
definitions for the Hasura GraphQL engine.

Example:

> > > from phlo\_hasura.plugin import HasuraServicePlugin
> > > plugin = HasuraServicePlugin()
> > > plugin.metadata.name
> > > 'hasura'
> > > service\_def = plugin.service\_definition

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;HasuraServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-hasura/phlo_hasura/plugin/HasuraServicePlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
