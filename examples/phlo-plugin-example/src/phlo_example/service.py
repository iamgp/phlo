"""Service plugin example."""

from phlo.plugins import PluginMetadata, ServicePlugin


class ExampleCacheServicePlugin(ServicePlugin):
    """Redis cache service plugin example."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="example_cache",
            version="1.0.0",
            description="Redis cache service for Phlo stacks",
            author="Phlo Team",
        )

    @property
    def service_definition(self) -> dict:
        return {
            "name": "example_cache",
            "category": "core",
            "default": False,
            "compose": {
                "image": "redis:7-alpine",
                "ports": ["6379:6379"],
                "healthcheck": {
                    "test": ["CMD", "redis-cli", "ping"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 5,
                },
            },
        }
