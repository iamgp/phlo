# publish_target (/docs/python-reference/packages/phlo-postgres/phlo_postgres/publish_target)



PostgreSQL publish target for data serving.

This module provides the PostgresPublishTarget class which serves as the
interface for publishing data to PostgreSQL. It wraps the PostgresResource
and provides configuration for the target schema where published data is stored.

The publish target is used by the phlo publishing system to route data to
PostgreSQL serving tables, typically in a "marts" or analytics schema.

Example:

> > > from phlo\_postgres import PostgresPublishTarget
> > > target = PostgresPublishTarget()
> > > print(target.default\_schema)
> > > marts
> > >
> > > Access the underlying resource for direct database operations [#access-the-underlying-resource-for-direct-database-operations]
> > >
> > > with target.resource as db:
> > > ...     db.execute("CREATE TABLE IF NOT EXISTS marts.summary (...)")

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PostgresPublishTarget&#x22;" href="&#x22;/docs/python-reference/packages/phlo-postgres/phlo_postgres/publish_target/PostgresPublishTarget&#x22;" />
    </Cards>
  </Tab>
</Tabs>
