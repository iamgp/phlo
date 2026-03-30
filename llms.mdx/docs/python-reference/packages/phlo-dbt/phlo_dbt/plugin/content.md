# plugin (/docs/python-reference/packages/phlo-dbt/phlo_dbt/plugin)



Phlo plugin implementations for dbt integration.

This module provides the Phlo plugin classes that register dbt capabilities
with the Phlo platform. It includes both an AssetProviderPlugin (for exposing
dbt models as Phlo assets) and a TransformationProviderPlugin (for dbt-based
data transformations).

Example:

> > > from phlo\_dbt.plugin import DbtAssetProvider, DbtTransformationProvider
> > >
> > > Get dbt assets [#get-dbt-assets]
> > >
> > > asset\_provider = DbtAssetProvider()
> > > assets = asset\_provider.get\_assets()
> > >
> > > Get transformation provider [#get-transformation-provider]
> > >
> > > transform\_provider = DbtTransformationProvider()
> > > cli\_plugin = transform\_provider.get\_cli\_plugin()

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DbtAssetProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/plugin/DbtAssetProvider&#x22;" />

      <Card title="&#x22;DbtTransformationProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/plugin/DbtTransformationProvider&#x22;" />
    </Cards>
  </Tab>
</Tabs>
