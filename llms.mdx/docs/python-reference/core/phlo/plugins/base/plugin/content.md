# plugin (/docs/python-reference/core/phlo/plugins/base/plugin)



Base plugin classes and metadata.

This module defines the core Plugin base class and PluginMetadata that all
plugin types must inherit from and implement. These classes form the foundation
of Phlo's plugin architecture, providing lifecycle management and metadata
description for all extensions.

Key Classes:

* :class:`PluginMetadata`: Plugin metadata container (name, version, etc.)
* :class:`Plugin`: Abstract base class for all plugin types

Plugin Lifecycle:

1. **Discovery**: Plugins are discovered via entry points
2. **Loading**: Plugin classes are instantiated
3. **Initialization**: :meth:`Plugin.initialize` is called with configuration
4. **Runtime**: Plugin provides its functionality
5. **Cleanup**: :meth:`Plugin.cleanup` is called when shutting down

Metadata Fields:
The :class:`PluginMetadata` dataclass captures all essential plugin
information including versioning, authorship, dependencies, and
capability requirements.

Example:

```python
from phlo.plugins.base import Plugin, PluginMetadata
from phlo.capabilities.support import CapabilitySupport

class MyConnector(Plugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my-connector",
            version="1.0.0",
            description="Connects to My Data Source",
            author="Jane Developer",
            license="MIT",
            homepage="https://github.com/example/my-connector",
            tags=["connector", "source"],
            dependencies=["requests>=2.25.0"],
            requires_capabilities=["query_engine"],
            optional_capabilities=["catalog"],
            support=CapabilitySupport(
                operational_guarantees=["best_effort"]
            )
        )

    def initialize(self, config: dict[str, Any]) -> None:
        # Connect to data source
        self.connection = create_connection(config)

    def cleanup(self) -> None:
        # Close connection
        self.connection.close()
```

Note:
This module should not be imported directly. Use the public exports
from :mod:`phlo.plugins.base` instead.

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PluginMetadata&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/base/plugin/PluginMetadata&#x22;" />

      <Card title="&#x22;Plugin&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/base/plugin/Plugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
