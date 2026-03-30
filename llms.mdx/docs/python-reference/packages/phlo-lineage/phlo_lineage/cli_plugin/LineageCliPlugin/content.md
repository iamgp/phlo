# LineageCliPlugin (/docs/python-reference/packages/phlo-lineage/phlo_lineage/cli_plugin/LineageCliPlugin)



Register lineage CLI commands with the plugin system.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for CLI command discovery.

  Provides identifying information for the Phlo CLI plugin system
  to recognize and load this command provider.

  Discovery:
  This metadata is used by the CLI framework to:

  * Identify the plugin uniquely
  * Display plugin information in help text
  * Enable plugin introspection and debugging

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = LineageCliPlugin()
    > > > meta = plugin.metadata
    > > > print(f"Plugin: \{meta.name} v\{meta.version}")
    > > > Plugin: lineage v0.1.0
    > > > print(meta.description)
    > > > Lineage CLI commands
  </Callout>
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Return click commands exposed by this plugin.

  Returns the lineage command group which contains all lineage-related
  subcommands registered under the 'phlo lineage' namespace.

  Command Group Structure:
  lineage (Group)
  ├── show (Command)
  ├── export (Command)
  ├── impact (Command)
  ├── status (Command)
  └── column (Group)
  ├── import-dbt (Command)
  ├── upstream (Command)
  └── downstream (Command)

  Registration:
  The CLI framework calls this method during plugin discovery and
  adds returned commands to the main phlo CLI hierarchy.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = LineageCliPlugin()
    > > > commands = plugin.get\_cli\_commands()
    > > > print(f"Registered \{len(commands)} command group(s)")
    > > > 1
    > > > cmd = commands\[0]
    > > > print(f"Group name: \{cmd.name}")
    > > > Group name: lineage
    > > > print(f"Subcommands: \{\[c.name for c in cmd.commands.values()]}")
    > > > Subcommands: \['show', 'export', 'impact', 'status', 'column']
  </Callout>

  <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
    phlo\_lineage.cli\_lineage.lineage\_group for the command implementation.
    click.Group for command group behavior.
  </Callout>

  <PySourceCode>
    ```python
    def get_cli_commands(self) -> list[click.Command]:
        """Return click commands exposed by this plugin.

                Returns the lineage command group which contains all lineage-related
        subcommands registered under the 'phlo lineage' namespace.

        Returns:
                    List containing the root lineage command group (click.Group).
                    The group includes subcommands: show, export, impact, status, and column.

                Command Group Structure:
                    lineage (Group)
                    ├── show (Command)
                    ├── export (Command)
                    ├── impact (Command)
                    ├── status (Command)
                    └── column (Group)
                        ├── import-dbt (Command)
                        ├── upstream (Command)
                        └── downstream (Command)

                Registration:
                    The CLI framework calls this method during plugin discovery and
                    adds returned commands to the main phlo CLI hierarchy.

        Example:
                    >>> plugin = LineageCliPlugin()
                    >>> commands = plugin.get_cli_commands()
                    >>> print(f"Registered {len(commands)} command group(s)")
                    1
                    >>> cmd = commands[0]
                    >>> print(f"Group name: {cmd.name}")
                    Group name: lineage
                    >>> print(f"Subcommands: {[c.name for c in cmd.commands.values()]}")
                    Subcommands: ['show', 'export', 'impact', 'status', 'column']

        See Also:
                    phlo_lineage.cli_lineage.lineage_group for the command implementation.
                    click.Group for command group behavior.

        """
        return [lineage_group]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List containing the root lineage command group (click.Group).
  </PyFunctionReturn>
</PyFunction>
