# DltCliPlugin (/docs/python-reference/packages/phlo-dlt/phlo_dlt/cli_plugin/DltCliPlugin)



Expose DLT CLI command groups to the Phlo plugin system.

CLI plugin that provides DLT-specific commands to the Phlo CLI.
Currently exposes workflow scaffolding commands.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Static plugin metadata for CLI discovery.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Return CLI commands contributed by this plugin.

  <PySourceCode>
    ```python
    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands contributed by this plugin.

        Returns:
            list[click.Command]: Registered top-level DLT CLI command groups.

        """
        return [workflow_group]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[click.Command]: Registered top-level DLT CLI command groups.
  </PyFunctionReturn>
</PyFunction>
