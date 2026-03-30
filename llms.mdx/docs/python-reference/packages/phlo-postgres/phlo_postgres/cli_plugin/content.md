# cli_plugin (/docs/python-reference/packages/phlo-postgres/phlo_postgres/cli_plugin)



CLI plugin for PostgreSQL commands.

This module provides the CLI plugin implementation that registers PostgreSQL
commands with the phlo CLI system. It exposes the postgres command group and
its subcommands (query, dump, restore, vacuum) to the main phlo CLI.

Example:

> > > from phlo\_postgres.cli\_plugin import PostgresCliPlugin
> > > plugin = PostgresCliPlugin()
> > > commands = plugin.get\_cli\_commands()
> > > print(commands\[0].name)
> > > postgres

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PostgresCliPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-postgres/phlo_postgres/cli_plugin/PostgresCliPlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
