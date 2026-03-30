# HasuraCliPlugin (/docs/python-reference/packages/phlo-hasura/phlo_hasura/cli_plugin/HasuraCliPlugin)



Register Hasura CLI commands with the plugin system.

This plugin integrates the Hasura command group into the Phlo CLI,
making all hasura subcommands available through `phlo hasura \<command>`.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for CLI command discovery.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = HasuraCliPlugin()
    > > > meta = plugin.metadata
    > > > print(meta.name)
    > > > hasura
  </Callout>
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Return click commands exposed by this plugin.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = HasuraCliPlugin()
    > > > commands = plugin.get\_cli\_commands()
    > > > len(commands)
    > > > 1
    > > > commands\[0].name
    > > > 'hasura'
  </Callout>

  <PySourceCode>
    ```python
    def get_cli_commands(self) -> list[click.Command]:
        """Return click commands exposed by this plugin.

        Returns:
            List containing the root Hasura command group.
            This group includes all hasura subcommands (track, relationships,
            permissions, auto_setup, export, apply, status, sync-permissions).

        Example:
            >>> plugin = HasuraCliPlugin()
            >>> commands = plugin.get_cli_commands()
            >>> len(commands)
            1
            >>> commands[0].name
            'hasura'

        """
        return [hasura]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List containing the root Hasura command group.
  </PyFunctionReturn>
</PyFunction>
