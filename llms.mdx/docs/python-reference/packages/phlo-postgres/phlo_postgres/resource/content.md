# resource (/docs/python-reference/packages/phlo-postgres/phlo_postgres/resource)



PostgreSQL connection resource with pooling for publishing and operational writes.

This module provides a lightweight, context-managed PostgreSQL resource that handles
connection pooling, transaction management, and health checks. It is designed for
operational writes and data publishing workflows.

Example:

> > > from phlo\_postgres import PostgresResource
> > >
> > > Context manager usage (recommended) [#context-manager-usage-recommended]
> > >
> > > with PostgresResource() as db:
> > > ...     db.execute("INSERT INTO logs (msg) VALUES (%s)", ("hello",))
> > > ...     rows = db.query("SELECT \* FROM logs")
> > > ...
> > >
> > > Manual lifecycle management [#manual-lifecycle-management]
> > >
> > > db = PostgresResource(host="localhost", port=5432)
> > > db.connect()
> > > if db.is\_healthy():
> > > ...     result = db.query\_one("SELECT COUNT(\*) FROM users")
> > > db.close()

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PostgresResource&#x22;" href="&#x22;/docs/python-reference/packages/phlo-postgres/phlo_postgres/resource/PostgresResource&#x22;" />
    </Cards>
  </Tab>
</Tabs>
