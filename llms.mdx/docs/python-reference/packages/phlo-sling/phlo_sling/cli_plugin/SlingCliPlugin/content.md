# SlingCliPlugin (/docs/python-reference/packages/phlo-sling/phlo_sling/cli_plugin/SlingCliPlugin)



Expose Sling CLI command groups to the Phlo plugin system.

This plugin class provides Sling-related CLI commands to the Phlo
command-line interface. It exposes commands for running replications,
listing connections, and discovering available streams.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Information about this plugin including
  name, version, and description.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Return CLI commands contributed by this plugin.

  Returns the list of Click command groups exposed by this plugin.
  These commands are mounted under the `phlo` CLI as subcommands.

  <PySourceCode>
    ```python
    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands contributed by this plugin.

        Returns the list of Click command groups exposed by this plugin.
        These commands are mounted under the ``phlo`` CLI as subcommands.

        Returns:
            List of Click Command objects contributed by this plugin.

        """
        return [sling_group]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of Click Command objects contributed by this plugin.
  </PyFunctionReturn>
</PyFunction>
