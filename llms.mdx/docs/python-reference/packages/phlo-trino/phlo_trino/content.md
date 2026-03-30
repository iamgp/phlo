# phlo_trino (/docs/python-reference/packages/phlo-trino/phlo_trino)



Phlo Trino package - Distributed SQL query engine integration.

This package provides Trino integration for the Phlo data platform,
including resource management, governance, and query capabilities.

Exports:
TrinoGovernanceBackend: Access control via SQL grants.
TrinoResourceProvider: Plugin providing Trino resources.
TrinoServicePlugin: Service plugin for Trino orchestration.
TrinoResource: Core resource for Trino connections and queries.
TrinoSettings: Configuration settings for Trino connections.
get\_settings: Cached settings factory function.

Example:

> > > from phlo\_trino import TrinoResource, get\_settings
> > > settings = get\_settings()
> > > trino = TrinoResource()
> > > results = trino.execute("SELECT \* FROM my\_table")

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['TrinoGovernanceBackend', 'TrinoResourceProvider', 'TrinoServicePlugin', 'TrinoResource', 'TrinoSettings', 'get_settings']&#x22;" />

<PyAttribute name="&#x22;__version__&#x22;" type="null" value="&#x22;'0.2.4'&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-trino/phlo_trino/plugin&#x22;" title="&#x22;plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-trino/phlo_trino/resource&#x22;" title="&#x22;resource&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-trino/phlo_trino/cli&#x22;" title="&#x22;cli&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-trino/phlo_trino/cli_plugin&#x22;" title="&#x22;cli_plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-trino/phlo_trino/publishing&#x22;" title="&#x22;publishing&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-trino/phlo_trino/observatory_plugin&#x22;" title="&#x22;observatory_plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-trino/phlo_trino/settings&#x22;" title="&#x22;settings&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-trino/phlo_trino/governance&#x22;" title="&#x22;governance&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-trino/phlo_trino/type_mapping&#x22;" title="&#x22;type_mapping&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-trino/phlo_trino/catalog_generator&#x22;" title="&#x22;catalog_generator&#x22;" />
    </Cards>
  </Tab>
</Tabs>
