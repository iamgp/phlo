# plugin (/docs/python-reference/packages/phlo-pgweb/phlo_pgweb/plugin)



Pgweb service plugin implementation.

This module provides the PgwebServicePlugin class which implements
a Phlo service plugin for pgweb, a web-based PostgreSQL database browser.

The plugin reads its Docker Compose service definition from a bundled YAML
file and exposes metadata for integration with Phlo's service management.

Example:

> > > from phlo\_pgweb.plugin import PgwebServicePlugin
> > > plugin = PgwebServicePlugin()
> > > print(plugin.metadata.name)
> > > pgweb
> > > service\_def = plugin.service\_definition

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PgwebServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pgweb/phlo_pgweb/plugin/PgwebServicePlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
