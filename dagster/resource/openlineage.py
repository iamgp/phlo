from dagster import ConfigurableResource
from openlineage.client import OpenLineageClient


class OpenLineageResource(ConfigurableResource):
    url: str = "http://marquez:5000"
    namespace: str = "lakehouse"

    def get_client(self) -> OpenLineageClient:
        return OpenLineageClient(url=self.url)
