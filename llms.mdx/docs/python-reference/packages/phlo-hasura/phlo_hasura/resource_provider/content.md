# resource_provider (/docs/python-reference/packages/phlo-hasura/phlo_hasura/resource_provider)



Resource provider plugin for phlo-hasura capabilities.

This module provides the HasuraResourceProvider class that exposes Hasura
as an API backend capability through the Phlo resource provider system.

The provider allows Hasura to be discovered and used as a swappable
GraphQL API backend by other components in the Phlo ecosystem.

Example:

> > > from phlo\_hasura.resource\_provider import HasuraResourceProvider
> > > provider = HasuraResourceProvider()
> > > backends = provider.get\_api\_backends()
> > > print(backends\[0].name)
> > > 'hasura'

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;HasuraResourceProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-hasura/phlo_hasura/resource_provider/HasuraResourceProvider&#x22;" />
    </Cards>
  </Tab>
</Tabs>
