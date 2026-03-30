# sources (/docs/python-reference/packages/phlo-core-plugins/phlo_core/sources)



Source connector plugins bundled with Phlo.

This module provides source connector plugins that enable Phlo to ingest
data from various external systems and APIs. Source connectors handle the
complexity of connecting to external data sources, authentication, and
data extraction.

Available Plugins:

* RestAPIPlugin: Generic REST API connector for fetching data from
  HTTP endpoints. Supports pagination, authentication headers,
  query parameters, and configurable timeouts.

Each plugin follows the SourceConnectorPlugin interface and provides methods
for fetching data and optionally retrieving schema information.

Example:
Import and use source plugins::

from phlo\_core.sources import RestAPIPlugin

Create the plugin [#create-the-plugin]

rest\_plugin = RestAPIPlugin()

Configure and fetch data [#configure-and-fetch-data]

config = \{
"url": "[https://api.example.com/users](https://api.example.com/users)",
"headers": \{"Authorization": "Bearer token123"},
"params": \{"limit": 100},
"timeout": 30,
"records\_path": "data.users"
}

for record in rest\_plugin.fetch\_data(config):
process(record)

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['RestAPIPlugin']&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-core-plugins/phlo_core/sources/rest_api&#x22;" title="&#x22;rest_api&#x22;" />
    </Cards>
  </Tab>
</Tabs>
