# PostgresExporterServicePlugin (/docs/python-reference/packages/phlo-postgres/phlo_postgres/plugin/PostgresExporterServicePlugin)



Service plugin for PostgreSQL Prometheus metrics exporter.

This plugin provides a Prometheus exporter service that exposes PostgreSQL
metrics for monitoring and alerting. It runs as a sidecar service alongside
the main PostgreSQL container.

Example:

> > > plugin = PostgresExporterServicePlugin()
> > > print(plugin.metadata.name)
> > > postgres-exporter

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for the PostgreSQL exporter service.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = PostgresExporterServicePlugin()
    > > > meta = plugin.metadata
    > > > print(meta.description)
    > > > Prometheus exporter for PostgreSQL metrics
  </Callout>
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Load the PostgreSQL exporter service definition from package data.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = PostgresExporterServicePlugin()
    > > > definition = plugin.service\_definition
  </Callout>
</PyAttribute>
