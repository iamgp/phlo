# PostgresCliPlugin (/docs/python-reference/packages/phlo-postgres/phlo_postgres/cli_plugin/PostgresCliPlugin)



CLI plugin that registers PostgreSQL commands with the phlo CLI.

This plugin provides the main entry point for PostgreSQL-related CLI
commands. It registers the postgres command group which includes
subcommands for querying, dumping, restoring, and maintaining PostgreSQL
databases.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for the PostgreSQL CLI plugin.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = PostgresCliPlugin()
    > > > meta = plugin.metadata
    > > > print(f"\{meta.name} v\{meta.version}")
    > > > postgres v0.1.0
    > > > print(meta.description)
    > > > CLI commands for PostgreSQL service access
  </Callout>
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Return CLI commands provided by this plugin.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = PostgresCliPlugin()
    > > > commands = plugin.get\_cli\_commands()
    > > > cmd = commands\[0]
    > > > print(cmd.name)
    > > > postgres
    > > > print(\[c.name for c in cmd.commands.values()])
    > > > \['query', 'dump', 'restore', 'vacuum']
  </Callout>

  <PySourceCode>
    ```python
    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands provided by this plugin.

        Returns:
            list[click.Command]: List of Click command objects to register
                with the main phlo CLI. Currently provides the postgres
                command group which includes query, dump, restore, and
                vacuum subcommands.

        Example:
            >>> plugin = PostgresCliPlugin()
            >>> commands = plugin.get_cli_commands()
            >>> cmd = commands[0]
            >>> print(cmd.name)
            postgres
            >>> print([c.name for c in cmd.commands.values()])
            ['query', 'dump', 'restore', 'vacuum']

        """
        return [postgres_group]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[click.Command]: List of Click command objects to register
    with the main phlo CLI. Currently provides the postgres
    command group which includes query, dump, restore, and
    vacuum subcommands.
  </PyFunctionReturn>
</PyFunction>
