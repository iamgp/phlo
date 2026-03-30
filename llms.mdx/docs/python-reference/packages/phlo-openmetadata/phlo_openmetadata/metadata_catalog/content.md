# metadata_catalog (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/metadata_catalog)



Metadata catalog provider for OpenMetadata.

Provides a capability-based interface for publishing metadata into OpenMetadata,
including tables, quality results, and lineage edges.

This module implements the MetadataCatalogSpec interface for OpenMetadata,
allowing it to be discovered and used by the phlo capability system.

Example:

> > > from phlo\_openmetadata.metadata\_catalog import OpenMetadataCatalogProvider
> > > provider = OpenMetadataCatalogProvider()
> > > provider.health\_check()
> > > True
> > > provider.upsert\_table(namespace="bronze", table=table\_obj)

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;OpenMetadataCatalogProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/metadata_catalog/OpenMetadataCatalogProvider&#x22;" />
    </Cards>
  </Tab>
</Tabs>
