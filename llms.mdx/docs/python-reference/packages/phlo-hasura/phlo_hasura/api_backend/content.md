# api_backend (/docs/python-reference/packages/phlo-hasura/phlo_hasura/api_backend)



Capability wrapper for Hasura as an API backend.

This module provides the HasuraApiBackend class that exposes Hasura's
GraphQL capabilities through a neutral API backend interface.

The backend handles health checks and provides metadata describing
the Hasura GraphQL endpoints available to consumers.

Example:

> > > from phlo\_hasura.api\_backend import HasuraApiBackend
> > > backend = HasuraApiBackend()
> > > backend.health\_check()
> > > True
> > > backend.describe()
> > > \{"service\_name": "hasura", "backend\_kind": "graphql", ...}

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;HasuraApiBackend&#x22;" href="&#x22;/docs/python-reference/packages/phlo-hasura/phlo_hasura/api_backend/HasuraApiBackend&#x22;" />
    </Cards>
  </Tab>
</Tabs>
