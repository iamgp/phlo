# PostgresPublishTarget (/docs/python-reference/packages/phlo-postgres/phlo_postgres/publish_target/PostgresPublishTarget)



Structured publish target for PostgreSQL serving tables.

This class provides a high-level interface for publishing data to PostgreSQL.
It encapsulates the database resource and configuration for the target schema
where published mart tables are stored.

The default schema is determined by the postgres\_mart\_schema setting, which
typically defaults to "marts" for serving analytics data.

Attributes [#attributes]

<PyAttribute name="&#x22;resource&#x22;" type="&#x22;PostgresResource&#x22;" value="&#x22;field(default_factory=PostgresResource)&#x22;">
  The PostgresResource instance for database operations.
  Automatically instantiated if not provided.
</PyAttribute>

<PyAttribute name="&#x22;target_system&#x22;" type="&#x22;str&#x22;" value="&#x22;'postgres'&#x22;">
  Identifier for the target system (always "postgres").
</PyAttribute>

<PyAttribute name="&#x22;default_schema&#x22;" type="&#x22;str&#x22;" value="null">
  Return the default serving schema for published mart tables.

  Retrieves the configured mart schema from settings, which determines
  where published tables should be created in the PostgreSQL database.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > target = PostgresPublishTarget()
    > > > schema = target.default\_schema
    > > > print(f"Publishing to schema: \{schema}")
    > > > Publishing to schema: marts
    > > >
    > > > Using the schema in DDL [#using-the-schema-in-ddl]
    > > >
    > > > with target.resource as db:
    > > > ...     db.ensure\_schema(schema)
    > > > ...     db.execute(f"CREATE TABLE \{schema}.users (...)")
  </Callout>
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, resource=PostgresResource(), target_system='postgres') -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;resource&#x22;" type="&#x22;PostgresResource&#x22;" value="&#x22;PostgresResource()&#x22;" />

    <PyParameter name="&#x22;target_system&#x22;" type="&#x22;str&#x22;" value="&#x22;'postgres'&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
