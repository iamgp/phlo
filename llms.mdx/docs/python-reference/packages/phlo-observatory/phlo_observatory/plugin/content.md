# plugin (/docs/python-reference/packages/phlo-observatory/phlo_observatory/plugin)



Observatory service plugin for container orchestration.

This module defines the ServicePlugin implementation for the Observatory UI,
enabling Docker Compose-based deployment and lifecycle management through
the Phlo service orchestration system.

The ObservatoryServicePlugin provides:

* Plugin metadata for discovery and versioning
* Service definition loading from package resources
* Integration with Phlo's service management CLI

Service Configuration:
The service definition is loaded from service.yaml in the package resources,
defining container images, ports, volumes, and environment variables.

Example:

> > > from phlo\_observatory.plugin import ObservatoryServicePlugin
> > > plugin = ObservatoryServicePlugin()
> > > print(plugin.metadata.name)
> > > 'observatory'
> > > service\_def = plugin.service\_definition

See Also:
phlo.plugins.ServicePlugin: Base class for service plugins.
phlo\_observatory.service.yaml: Service definition configuration.

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;ObservatoryServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-observatory/phlo_observatory/plugin/ObservatoryServicePlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
