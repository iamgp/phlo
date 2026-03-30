# AlertingCliPlugin (/docs/python-reference/packages/phlo-alerting/phlo_alerting/cli_plugin/AlertingCliPlugin)



Expose alerting commands to the Phlo CLI plugin system.

CLI plugin implementation that registers the alerts command group
with the Phlo CLI. Provides commands for testing, listing, and
checking the status of alert destinations.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Plugin identity and discovery information.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Return CLI commands provided by the alerting plugin.

  Returns the Click command group containing all alerting subcommands.
  This group is registered with the main Phlo CLI.

  <PySourceCode>
    ```python
    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands provided by the alerting plugin.

        Returns the Click command group containing all alerting subcommands.
        This group is registered with the main Phlo CLI.

        Returns:
            Ordered list of alerting Click commands (currently just alerts_group).

        Examples:
            >>> plugin = AlertingCliPlugin()
            >>> commands = plugin.get_cli_commands()
            >>> len(commands)
            1
            >>> commands[0].name
            'alerts'

        """
        return [alerts_group]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    Ordered list of alerting Click commands (currently just alerts\_group).
  </PyFunctionReturn>
</PyFunction>
