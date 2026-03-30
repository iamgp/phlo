# PostgresVolumeSetupServicePlugin (/docs/python-reference/packages/phlo-postgres/phlo_postgres/plugin/PostgresVolumeSetupServicePlugin)



Service plugin for PostgreSQL data volume permission setup.

This plugin provides an initialization service that ensures proper
ownership and permissions on PostgreSQL data volumes before the main
database container starts. This is particularly important for bind mounts
on systems with strict permission requirements.

Example:

> > > plugin = PostgresVolumeSetupServicePlugin()
> > > print(plugin.metadata.name)
> > > postgres-volume-setup

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for the PostgreSQL volume setup service.
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Load the PostgreSQL volume setup service definition from package data.
</PyAttribute>
