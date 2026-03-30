# dagster_ext (/docs/python-reference/packages/phlo-dagster/phlo_dagster/dagster_ext)



Dagster extension plugin classes for Phlo.

This module defines the plugin architecture for extending Dagster functionality
within Phlo. It provides base classes for plugins that contribute Dagster
definitions, resources, and custom functionality to the orchestration layer.

Plugin Architecture:

* DagsterExtensionPlugin: Base class for all Dagster extensions
* IngestionEnginePlugin: Deprecated base for ingestion plugins

Plugins are discovered via entry\_points (group: phlo.plugins.dagster) and
automatically merged into global definitions.

Extension Points:

* get\_definitions(): Return Dagster definitions to merge
* get\_exports(): Expose symbols to phlo.\* public API
* clear\_registries(): Clean up for reloads and testing

Registration:
Plugins register via setuptools entry\_points::

\[phlo.plugins.dagster]
my\_plugin = my\_package.plugin:MyExtensionPlugin

Lifecycle:

1. Discovery via entry\_points
2. Instantiation and type validation
3. get\_definitions() called during framework initialization
4. Definitions merged into global Definitions object

Example:
Creating a custom extension::

from phlo\_dagster.dagster\_ext import DagsterExtensionPlugin
import dagster as dg

class MyExtension(DagsterExtensionPlugin):
def get\_definitions(self):
@dg.asset
def my\_custom\_asset():
return "data"

return dg.Definitions(assets=\[my\_custom\_asset])

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DagsterExtensionPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/dagster_ext/DagsterExtensionPlugin&#x22;" />

      <Card title="&#x22;IngestionEnginePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/dagster_ext/IngestionEnginePlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
