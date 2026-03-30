# PostgrestCliPlugin (/docs/python-reference/packages/phlo-postgrest/phlo_postgrest/cli_plugin/PostgrestCliPlugin)



Register PostgREST CLI commands with the Phlo plugin system.

This plugin bridges the phlo\_postgrest CLI commands with Phlo's
plugin architecture, exposing view generation and authentication
setup as subcommands under the `phlo postgrest` namespace.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Plugin identification and version.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Return CLI commands exposed by this plugin.

  <PySourceCode>
    ```python
    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands exposed by this plugin.

        Returns:
            list[click.Command]: Registered PostgREST command group.

        """
        return [postgrest]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[click.Command]: Registered PostgREST command group.
  </PyFunctionReturn>
</PyFunction>
