# resource_provider (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/resource_provider)



Resource provider plugin for OpenMetadata capabilities.

Exposes OpenMetadata as a metadata catalog capability that can be discovered
and used by the phlo capability system for publishing metadata, lineage,
and quality results.

Example:

> > > from phlo\_openmetadata.resource\_provider import OpenMetadataResourceProvider
> > > provider = OpenMetadataResourceProvider()
> > > catalogs = provider.get\_metadata\_catalogs()
> > > len(catalogs)
> > > 1

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;OpenMetadataResourceProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/resource_provider/OpenMetadataResourceProvider&#x22;" />
    </Cards>
  </Tab>
</Tabs>
