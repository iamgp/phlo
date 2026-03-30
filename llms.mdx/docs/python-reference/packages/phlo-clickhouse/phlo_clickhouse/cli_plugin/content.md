# cli_plugin (/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/cli_plugin)



CLI plugin for ClickHouse commands.

This module provides a CLI plugin that registers ClickHouse-specific commands
with the Phlo CLI framework, enabling users to interact with ClickHouse
databases directly from the command line.

Example:
The plugin is automatically discovered by Phlo's plugin system:

> > > from phlo\_clickhouse.cli\_plugin import ClickHouseCliPlugin
> > > plugin = ClickHouseCliPlugin()
> > > plugin.metadata.name
> > > 'clickhouse'

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;ClickHouseCliPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/cli_plugin/ClickHouseCliPlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
