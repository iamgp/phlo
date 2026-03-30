# OpenMetadataCliPlugin (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/cli_plugin/OpenMetadataCliPlugin)



CLI plugin that registers OpenMetadata commands.

This plugin integrates OpenMetadata CLI commands into the Phlo CLI,
providing health checks and sync functionality.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  PluginMetadata containing plugin identification information.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Get CLI commands exposed by this plugin.

  <PySourceCode>
    ```python
    def get_cli_commands(self) -> list[click.Command]:
        """Get CLI commands exposed by this plugin.

        Returns:
            list[click.Command]: Registered OpenMetadata CLI commands
                (health, sync, etc.).

        """
        return [openmetadata]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[click.Command]: Registered OpenMetadata CLI commands
    (health, sync, etc.).
  </PyFunctionReturn>
</PyFunction>
