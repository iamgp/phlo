# phlo_postgres (/docs/python-reference/packages/phlo-postgres/phlo_postgres)



Phlo PostgreSQL metadata store package.

This package provides the PostgreSQL integration for Phlo, including:

* Service plugin for managing PostgreSQL containers
* Resource management with connection pooling
* CLI commands for database operations
* Configuration settings management
* Publish targets for serving data

Example:

> > > from phlo\_postgres import PostgresResource, get\_settings
> > > settings = get\_settings()
> > > with PostgresResource() as db:
> > > ...     rows = db.query("SELECT \* FROM users LIMIT 10")

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['PostgresPublishTarget', 'PostgresResource', 'PostgresServicePlugin', 'PostgresSettings', 'get_settings']&#x22;" />

<PyAttribute name="&#x22;__version__&#x22;" type="null" value="&#x22;'0.2.4'&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-postgres/phlo_postgres/plugin&#x22;" title="&#x22;plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-postgres/phlo_postgres/resource&#x22;" title="&#x22;resource&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-postgres/phlo_postgres/cli&#x22;" title="&#x22;cli&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-postgres/phlo_postgres/publish_target&#x22;" title="&#x22;publish_target&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-postgres/phlo_postgres/cli_plugin&#x22;" title="&#x22;cli_plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-postgres/phlo_postgres/settings&#x22;" title="&#x22;settings&#x22;" />
    </Cards>
  </Tab>
</Tabs>
