# plugin (/docs/python-reference/packages/phlo-postgres/phlo_postgres/plugin)



PostgreSQL service plugin implementations.

This module provides plugin implementations that integrate PostgreSQL with the
phlo plugin system. It includes service plugins for the PostgreSQL database,
Prometheus exporter, and volume setup, as well as a resource provider plugin
that exposes PostgreSQL capabilities to the rest of the system.

Example:

> > > from phlo\_postgres.plugin import PostgresServicePlugin
> > > plugin = PostgresServicePlugin()
> > > print(plugin.metadata.name)
> > > postgres
> > > definition = plugin.service\_definition

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PostgresServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-postgres/phlo_postgres/plugin/PostgresServicePlugin&#x22;" />

      <Card title="&#x22;PostgresExporterServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-postgres/phlo_postgres/plugin/PostgresExporterServicePlugin&#x22;" />

      <Card title="&#x22;PostgresVolumeSetupServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-postgres/phlo_postgres/plugin/PostgresVolumeSetupServicePlugin&#x22;" />

      <Card title="&#x22;PostgresResourceProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-postgres/phlo_postgres/plugin/PostgresResourceProvider&#x22;" />
    </Cards>
  </Tab>
</Tabs>
