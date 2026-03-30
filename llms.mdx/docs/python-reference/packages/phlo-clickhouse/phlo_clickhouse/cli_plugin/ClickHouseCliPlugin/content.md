# ClickHouseCliPlugin (/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/cli_plugin/ClickHouseCliPlugin)



Register ClickHouse CLI commands with the Phlo CLI.

This plugin integrates ClickHouse commands into the Phlo CLI, providing
access to query execution, status checks, and other ClickHouse operations.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for CLI registration.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = ClickHouseCliPlugin()
    > > > meta = plugin.metadata
    > > > meta.name
    > > > 'clickhouse'
  </Callout>
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Return list of ClickHouse CLI command groups.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = ClickHouseCliPlugin()
    > > > commands = plugin.get\_cli\_commands()
    > > > \[cmd.name for cmd in commands]
    > > > \['clickhouse']
  </Callout>

  <PySourceCode>
    ```python
    def get_cli_commands(self) -> list[click.Command]:
        """Return list of ClickHouse CLI command groups.

        Returns:
            List containing the clickhouse command group.

        Example:
            >>> plugin = ClickHouseCliPlugin()
            >>> commands = plugin.get_cli_commands()
            >>> [cmd.name for cmd in commands]
            ['clickhouse']

        """
        return [clickhouse_group]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List containing the clickhouse command group.
  </PyFunctionReturn>
</PyFunction>
