# phlo_openmetadata (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata)



Phlo OpenMetadata integration package.

This package provides the OpenMetadata catalog integration for Phlo,
enabling metadata synchronization, lineage tracking, and quality
check publishing to an OpenMetadata data catalog.

Key components:

* OpenMetadataClient: REST API client for OpenMetadata
* OpenMetadataSettings: Configuration management
* QualityCheckPublisher: Publishes quality checks to OM
* DbtManifestParser: Syncs dbt documentation to OM
* LineageExtractor: Extracts and publishes lineage

Example:

> > > from phlo\_openmetadata import OpenMetadataClient, get\_settings
> > > settings = get\_settings()
> > > client = OpenMetadataClient(
> > > ...     base\_url=settings.openmetadata\_uri(),
> > > ...     username=settings.openmetadata\_username,
> > > ...     password=settings.openmetadata\_password,
> > > ... )
> > > client.health\_check()
> > > True

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['DbtManifestParser', 'OpenMetadataSettings', 'OpenMetadataClient', 'OpenMetadataColumn', 'OpenMetadataLineageEdge', 'OpenMetadataTable', 'get_settings']&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/cli_openmetadata&#x22;" title="&#x22;cli_openmetadata&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/graph&#x22;" title="&#x22;graph&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/plugin&#x22;" title="&#x22;plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/dbt_sync&#x22;" title="&#x22;dbt_sync&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/cli_plugin&#x22;" title="&#x22;cli_plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/settings&#x22;" title="&#x22;settings&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/hooks_plugin&#x22;" title="&#x22;hooks_plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/metadata_catalog&#x22;" title="&#x22;metadata_catalog&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/resource_provider&#x22;" title="&#x22;resource_provider&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/openmetadata&#x22;" title="&#x22;openmetadata&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/lineage&#x22;" title="&#x22;lineage&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/capabilities&#x22;" title="&#x22;capabilities&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/quality_sync&#x22;" title="&#x22;quality_sync&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/nessie_sync&#x22;" title="&#x22;nessie_sync&#x22;" />
    </Cards>
  </Tab>
</Tabs>
