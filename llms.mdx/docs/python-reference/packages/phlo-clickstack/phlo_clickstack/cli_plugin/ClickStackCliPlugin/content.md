# ClickStackCliPlugin (/docs/python-reference/packages/phlo-clickstack/phlo_clickstack/cli_plugin/ClickStackCliPlugin)



Register ClickStack CLI commands.

This plugin provides CLI commands for querying and managing the
ClickStack ClickHouse service instance.

Example:
Registered automatically when phlo\_clickstack is installed.
Use `phlo clickstack --help` to see available commands.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for ClickStack CLI registration.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Return ClickStack CLI commands.

  <PySourceCode>
    ```python
    def get_cli_commands(self) -> list[click.Command]:
        """Return ClickStack CLI commands.

        Returns:
            list[click.Command]: List of Click commands provided by this plugin.

        """
        return [clickstack_group]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[click.Command]: List of Click commands provided by this plugin.
  </PyFunctionReturn>
</PyFunction>
