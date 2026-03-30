# plugin (/docs/python-reference/packages/phlo-grafana/phlo_grafana/plugin)



Grafana service plugin implementation.

This module provides the GrafanaServicePlugin class, which integrates Grafana
as a managed service within the Phlo platform. The plugin handles service
metadata registration, service definition loading, and lifecycle management.

The plugin loads its Docker Compose service configuration from a local YAML
file, allowing for consistent deployment across environments.

Example:

> > > from phlo\_grafana.plugin import GrafanaServicePlugin
> > > plugin = GrafanaServicePlugin()
> > > print(plugin.metadata.name)
> > > 'grafana'
> > > print(plugin.metadata.tags)
> > > \['observability', 'metrics', 'dashboards']

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;GrafanaServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-grafana/phlo_grafana/plugin/GrafanaServicePlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
