# DbtTransformationProvider (/docs/python-reference/packages/phlo-dbt/phlo_dbt/plugin/DbtTransformationProvider)



Transformation provider plugin for dbt.

This plugin registers dbt as a transformation provider in Phlo, enabling
dbt models to be executed as part of Phlo's data pipeline transformations.

The provider supplies both the asset retriever (for discovering transformable
assets) and the CLI plugin (for dbt-related CLI commands). This allows Phlo
to integrate dbt runs into its orchestration and provide unified CLI access
to dbt operations.

Example:

> > > from phlo\_dbt.plugin import DbtTransformationProvider
> > > provider = DbtTransformationProvider()
> > >
> > > Get metadata [#get-metadata]
> > >
> > > metadata = provider.metadata
> > > print(f"Transform Provider: \{metadata.name}")
> > >
> > > Get asset retriever function [#get-asset-retriever-function]
> > >
> > > retriever = provider.get\_asset\_retriever()
> > > assets = retriever()
> > >
> > > Get CLI plugin for dbt commands [#get-cli-plugin-for-dbt-commands]
> > >
> > > cli = provider.get\_cli\_plugin()
> > > commands = cli.get\_cli\_commands()

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_asset_retriever&#x22;" type="&#x22;(self)&#x22;">
  Return a function to retrieve transformation asset specs.

  <PySourceCode>
    ```python
    def get_asset_retriever(self):
        """Return a function to retrieve transformation asset specs.

        Returns:
            Callable that returns dbt asset specifications.

        """
        return build_dbt_asset_specs
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="null">
    Callable that returns dbt asset specifications.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_cli_plugin&#x22;" type="&#x22;(self)&#x22;">
  Return the CLI plugin for dbt commands.

  <PySourceCode>
    ```python
    def get_cli_plugin(self):
        """Return the CLI plugin for dbt commands.

        Returns:
            DbtCliPlugin instance for dbt CLI command integration.

        """
        from phlo_dbt.cli_plugin import DbtCliPlugin

        return DbtCliPlugin
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="null">
    DbtCliPlugin instance for dbt CLI command integration.
  </PyFunctionReturn>
</PyFunction>
