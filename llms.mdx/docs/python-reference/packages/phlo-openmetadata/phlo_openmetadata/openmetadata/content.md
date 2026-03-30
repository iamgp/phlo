# openmetadata (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/openmetadata)



OpenMetadata REST API client for metadata synchronization.

Provides authenticated access to OpenMetadata for:

* Creating/updating table entities
* Publishing lineage information
* Managing quality test results
* Syncing column-level documentation

Example:

> > > from phlo\_openmetadata import OpenMetadataClient, OpenMetadataSettings
> > > settings = OpenMetadataSettings()
> > > client = OpenMetadataClient(
> > > ...     base\_url=settings.openmetadata\_uri(),
> > > ...     username=settings.openmetadata\_username,
> > > ...     password=settings.openmetadata\_password,
> > > ... )
> > > client.health\_check()
> > > True
> > > client.create\_or\_update\_table("bronze", table\_obj)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;OpenMetadataColumn&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/openmetadata/OpenMetadataColumn&#x22;" />

      <Card title="&#x22;OpenMetadataTable&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/openmetadata/OpenMetadataTable&#x22;" />

      <Card title="&#x22;OpenMetadataLineageEdge&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/openmetadata/OpenMetadataLineageEdge&#x22;" />

      <Card title="&#x22;OpenMetadataClient&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/openmetadata/OpenMetadataClient&#x22;" />
    </Cards>
  </Tab>
</Tabs>
