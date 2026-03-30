# base (/docs/python-reference/core/phlo/plugins/base)



Base classes for Phlo plugins.

This module defines the abstract base classes that all plugin types must inherit
from and implement. These interfaces provide a standardized contract for extending
Phlo's functionality through plugins.

Plugin Types:

* :class:`Plugin`: Base class for all plugins
* :class:`SourceConnectorPlugin`: Data source connectors
* :class:`QualityCheckPlugin`: Data quality validation
* :class:`QualityProviderPlugin`: Quality check providers
* :class:`IngestionProviderPlugin`: Data ingestion providers
* :class:`TransformationPlugin`: Data transformation tools
* :class:`TransformationProviderPlugin`: Transformation providers
* :class:`ServicePlugin`: Infrastructure services
* :class:`CatalogPlugin`: Metadata catalogs
* :class:`GovernancePlugin`: Data governance features
* :class:`AssetProviderPlugin`: Asset definitions
* :class:`ResourceProviderPlugin`: Resource definitions
* :class:`OrchestratorAdapterPlugin`: Orchestrator integrations
* :class:`CliCommandPlugin`: CLI command extensions

Each plugin type defines:

* :attr:`PluginMetadata`: Plugin metadata (name, version, description)
* :meth:`Plugin.initialize`: Lifecycle initialization
* :meth:`Plugin.cleanup`: Lifecycle cleanup
* Type-specific abstract methods

Example:

```python
from phlo.plugins.base import Plugin, PluginMetadata
from phlo.capabilities.support import CapabilitySupport

class MyPlugin(Plugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my-plugin",
            version="1.0.0",
            description="A custom Phlo plugin",
            author="My Name",
            support=CapabilitySupport()
        )

    def initialize(self, config: dict) -> None:
        # Setup connections, load resources
        pass
```

See Also:

* :mod:`phlo.plugins.discovery`: Plugin discovery and loading
* :mod:`phlo.capabilities`: Capability system for plugins

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['Plugin', 'PluginMetadata', 'CliCommandPlugin', 'SourceConnectorPlugin', 'QualityCheckPlugin', 'QualityProviderPlugin', 'IngestionProviderPlugin', 'TransformationPlugin', 'TransformationProviderPlugin', 'ServicePlugin', 'CatalogPlugin', 'GovernancePlugin', 'AssetProviderPlugin', 'ResourceProviderPlugin', 'OrchestratorAdapterPlugin']&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/base/plugin&#x22;" title="&#x22;plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/base/cli&#x22;" title="&#x22;cli&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/base/catalog&#x22;" title="&#x22;catalog&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/base/quality_provider&#x22;" title="&#x22;quality_provider&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/base/providers&#x22;" title="&#x22;providers&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/base/quality&#x22;" title="&#x22;quality&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/base/governance&#x22;" title="&#x22;governance&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/base/transformation_provider&#x22;" title="&#x22;transformation_provider&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/base/source&#x22;" title="&#x22;source&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/base/transform&#x22;" title="&#x22;transform&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/base/ingestion_provider&#x22;" title="&#x22;ingestion_provider&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/base/orchestrator&#x22;" title="&#x22;orchestrator&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/base/service&#x22;" title="&#x22;service&#x22;" />
    </Cards>
  </Tab>
</Tabs>
