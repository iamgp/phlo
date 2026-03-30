# source (/docs/python-reference/core/phlo/plugins/base/source)



Source connector plugin classes.

This module defines the :class:`SourceConnectorPlugin` base class for implementing
data source connectors. Source connectors enable Phlo to ingest data from external
systems like APIs, databases, file systems, and message queues.

Source connectors are responsible for:

* Connecting to external data sources
* Fetching data in record-by-record fashion
* Providing schema information when available
* Testing connectivity before ingestion

Example Implementations:

* HTTP API connectors (REST, GraphQL)
* Database connectors (PostgreSQL, MySQL, etc.)
* File system connectors (CSV, JSON, Parquet)
* Message queue connectors (Kafka, RabbitMQ)
* Cloud storage connectors (S3, GCS, Azure Blob)

Key Methods:

* :meth:`fetch_data`: Required. Yields records from the source
* :meth:`get_schema`: Optional. Returns column type mapping
* :meth:`test_connection`: Optional. Validates connectivity

See Also:

* :class:`IngestionProviderPlugin`: For advanced ingestion customization
* :mod:`phlo.ingestion`: Public API for ingestion operations

Example:

```python
from phlo.plugins.base import SourceConnectorPlugin, PluginMetadata
from collections.abc import Iterator
import requests

class JSONPlaceholderConnector(SourceConnectorPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="jsonplaceholder",
            version="1.0.0",
            description="Fetch posts from JSONPlaceholder API",
            author="Example Author",
        )

    def fetch_data(self, config: dict[str, Any]) -> Iterator[dict[str, Any]]:
        endpoint = config.get("endpoint", "posts")
        response = requests.get(f"https://jsonplaceholder.typicode.com/\{endpoint\}")
        response.raise_for_status()
        for item in response.json():
            yield item

    def get_schema(self, config: dict[str, Any]) -> dict[str, str]:
        return \{
            "userId": "int",
            "id": "int",
            "title": "string",
            "body": "string",
        \}
```

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;SourceConnectorPlugin&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/base/source/SourceConnectorPlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
