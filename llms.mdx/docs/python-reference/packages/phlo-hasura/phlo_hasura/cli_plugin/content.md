# cli_plugin (/docs/python-reference/packages/phlo-hasura/phlo_hasura/cli_plugin)



CLI plugin for Hasura commands.

This module provides the HasuraCliPlugin class that registers Hasura CLI commands
with the Phlo plugin system. It exposes the `hasura` command group to the main
Phlo CLI.

Example:
The plugin is automatically discovered and loaded by the plugin system:

> > > from phlo\_hasura.cli\_plugin import HasuraCliPlugin
> > > plugin = HasuraCliPlugin()
> > > commands = plugin.get\_cli\_commands()

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;HasuraCliPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-hasura/phlo_hasura/cli_plugin/HasuraCliPlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
