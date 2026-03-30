# DbtAssetProvider (/docs/python-reference/packages/phlo-dbt/phlo_dbt/plugin/DbtAssetProvider)



Asset provider plugin exposing dbt models as Phlo assets.

This plugin discovers dbt models from the project's manifest and exposes
them as Phlo AssetSpec objects. This enables dbt models to participate in
Phlo's orchestration, lineage tracking, and monitoring systems.

The plugin uses the build\_dbt\_asset\_specs() function to parse the dbt
manifest and create corresponding asset specifications with proper
dependencies, metadata, and execution configuration.

Example:

> > > from phlo\_dbt.plugin import DbtAssetProvider
> > > provider = DbtAssetProvider()
> > >
> > > Get plugin metadata [#get-plugin-metadata]
> > >
> > > metadata = provider.metadata
> > > print(f"Plugin: \{metadata.name} v\{metadata.version}")
> > >
> > > Get dbt assets [#get-dbt-assets]
> > >
> > > assets = provider.get\_assets()
> > > for asset in assets:
> > > ...     print(f"Asset: \{asset.key}, Group: \{asset.group}")

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_assets&#x22;" type="&#x22;(self) -> Iterable[AssetSpec]&#x22;">
  Return dbt-derived asset specifications.

  <PySourceCode>
    ```python
    def get_assets(self) -> Iterable[AssetSpec]:
        """Return dbt-derived asset specifications.

        Returns:
            Iterable of dbt asset specifications.

        """
        return build_dbt_asset_specs()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable&#x22;">
    Iterable of dbt asset specifications.
  </PyFunctionReturn>
</PyFunction>
