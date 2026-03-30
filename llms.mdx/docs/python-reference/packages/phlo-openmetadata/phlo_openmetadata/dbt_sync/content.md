# dbt_sync (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/dbt_sync)



dbt manifest parser and synchronizer.

Parses dbt manifest.json and catalog.json to extract model documentation,
column descriptions, and tests for syncing to OpenMetadata.

This module enables bi-directional sync between dbt projects and OpenMetadata,
ensuring documentation and lineage are consistent across both systems.

Example:

> > > from phlo\_openmetadata.dbt\_sync import DbtManifestParser
> > > parser = DbtManifestParser(
> > > ...     manifest\_path="target/manifest.json",
> > > ...     catalog\_path="target/catalog.json",
> > > ... )
> > > manifest = parser.load\_manifest()
> > > models = parser.get\_models(manifest)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DbtManifestParser&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/dbt_sync/DbtManifestParser&#x22;" />
    </Cards>
  </Tab>
</Tabs>
