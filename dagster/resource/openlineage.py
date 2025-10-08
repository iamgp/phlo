from dagster import ConfigurableResource
from openlineage.client import OpenLineageClient
from openlineage.client.transport.http import HttpTransport


class OpenLineageResource(ConfigurableResource):
    url: str = "http://marquez:5000"
    namespace: str = "lakehouse"

    def get_client(self) -> OpenLineageClient:
        transport = HttpTransport(url=self.url)
        return OpenLineageClient(transport=transport)
