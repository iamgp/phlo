# PanderaCliPlugin (/docs/python-reference/packages/phlo-pandera/phlo_pandera/cli_plugin/PanderaCliPlugin)



Register quality validation and schema commands with the CLI.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for quality CLI commands.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Return CLI commands exposed by this plugin.

  <PySourceCode>
    ```python
    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands exposed by this plugin.

        Returns:
            list[click.Command]: Quality command set registered by the plugin.

        """
        return [schema, validate_schema, validate_workflow]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[click.Command]: Quality command set registered by the plugin.
  </PyFunctionReturn>
</PyFunction>
