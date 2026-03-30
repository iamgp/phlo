# plugins (/docs/python-reference/core/phlo/plugins)



Phlo Plugin System

Enable community contributions through a plugin architecture.

Phlo provides a plugin system that allows developers to extend
the framework with custom:

* Source connectors (ingest data from new APIs/databases)
* Quality checks (custom validation logic)
* Transformations (custom data processing steps)
* Services (Docker-based infrastructure components)

Plugin Types [#plugin-types]

1\. Source Connector Plugins [#1-source-connector-plugins]

Extend Phlo with new data sources (APIs, databases, file formats).

```python
from phlo.plugins import SourceConnectorPlugin

class MyAPIConnector(SourceConnectorPlugin):
    name = "my_api"
    version = "1.0.0"

    def fetch_data(self, config: dict) -> Iterator[dict]:
        # Implement data fetching logic
        pass
```

2\. Quality Check Plugins [#2-quality-check-plugins]

Add custom quality check types beyond the built-in checks.

```python
from phlo.plugins import QualityCheckPlugin

class CustomQualityCheck(QualityCheckPlugin):
    name = "custom_check"
    version = "1.0.0"

    def validate(self, df: pd.DataFrame) -> QualityCheckResult:
        # Implement custom validation logic
        pass
```

3\. Transformation Plugins [#3-transformation-plugins]

Add custom transformation functions.

```python
from phlo.plugins import TransformationPlugin

class CustomTransform(TransformationPlugin):
    name = "custom_transform"
    version = "1.0.0"

    def transform(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        # Implement transformation logic
        pass
```

4\. Service Plugins [#4-service-plugins]

Add Docker-based infrastructure components.

```python
from phlo.plugins import ServicePlugin

class CustomService(ServicePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="custom_service",
            version="1.0.0",
            description="Custom service",
        )

    @property
    def service_definition(self) -> dict:
        return \{
            "category": "custom",
            "compose": \{
                "image": "my-service:latest",
                "ports": ["1234:1234"],
            \},
        \}
```

Installing Plugins [#installing-plugins]

Plugins are installed as Python packages with entry points:

```toml
# Plugin package's pyproject.toml
[project.entry-points."phlo.plugins.sources"]
my_api = "my_phlo_plugin:MyAPIConnector"

[project.entry-points."phlo.plugins.quality"]
custom_check = "my_phlo_plugin:CustomQualityCheck"

[project.entry-points."phlo.plugins.transforms"]
custom_transform = "my_phlo_plugin:CustomTransform"

[project.entry-points."phlo.plugins.services"]
custom_service = "my_phlo_plugin:CustomService"
```

After installing the plugin package:

```bash
pip install my-phlo-plugin
```

The plugin is automatically discovered and available:

```python
from phlo.plugins import discover_plugins

# Discover all installed plugins
plugins = discover_plugins()

# Use plugin
from phlo.plugins import get_source_connector
connector = get_source_connector("my_api")
data = connector.fetch_data(config=\{...\})
```

Plugin Development Guide [#plugin-development-guide]

See docs/PLUGIN\_DEVELOPMENT.md for complete guide on developing plugins.

Security [#security]

Plugins are loaded from installed Python packages only. Ensure you:

* Only install trusted plugins
* Review plugin source code before installation
* Use virtual environments to isolate plugins

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['Plugin', 'PluginMetadata', 'SourceConnectorPlugin', 'QualityCheckPlugin', 'QualityProviderPlugin', 'ServicePlugin', 'TransformationPlugin', 'AssetProviderPlugin', 'CatalogPlugin', 'ResourceProviderPlugin', 'OrchestratorAdapterPlugin', 'HookPlugin', 'HookProvider', 'HookHandler', 'HookFilter', 'FailurePolicy', 'ObservatoryExtensionPlugin', 'ObservatoryExtensionManifest', 'ObservatoryExtensionCompatibility', 'ObservatoryExtensionSettings', 'ObservatoryExtensionRoute', 'ObservatoryExtensionNavItem', 'ObservatoryExtensionSlot', 'ObservatoryExtensionSettingsPanel', 'ObservatoryExtensionUI', 'discover_observatory_extensions', 'get_observatory_extension', 'SettingsScope', 'SettingsRecord', 'SettingsService', 'get_settings_service', 'SemanticLayerProvider', 'SemanticModel', 'discover_plugins', 'list_plugins', 'get_plugin', 'get_plugin_info', 'get_source_connector', 'get_quality_check', 'get_quality_provider', 'get_ingestion_provider', 'get_transformation', 'get_transformation_provider', 'get_service', 'validate_plugins', 'PluginRegistry']&#x22;" />

<PyAttribute name="&#x22;__version__&#x22;" type="null" value="&#x22;'0.7.9'&#x22;" />

<Tabs items="[&#x22;Functions&#x22;,&#x22;Modules&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;__getattr__&#x22;" type="&#x22;(name)&#x22;">
      Lazily expose discovery symbols to avoid import cycles.

      <PySourceCode>
        ```python
        def __getattr__(name):
            """Lazily expose discovery symbols to avoid import cycles.

            Args:
                name: Attribute name requested from this module.

            Returns:
                Resolved symbol from `phlo.plugins.discovery`.

            Raises:
                AttributeError: If the attribute is not a supported lazy export.
            """
            if name in [
                "discover_plugins",
                "get_plugin",
                "get_plugin_info",
                "get_quality_check",
                "get_quality_provider",
                "get_ingestion_provider",
                "get_service",
                "get_hook_plugin",
                "get_source_connector",
                "get_transformation",
                "get_transformation_provider",
                "list_plugins",
                "validate_plugins",
                "PluginRegistry",
            ]:
                import phlo.plugins.discovery

                return getattr(phlo.plugins.discovery, name)
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="null" value="undefined">
          Attribute name requested from this module.
        </PyParameter>
      </div>

      <PyFunctionReturn type="null">
        Resolved symbol from `phlo.plugins.discovery`.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>

  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/observatory_settings&#x22;" title="&#x22;observatory_settings&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/registry_client&#x22;" title="&#x22;registry_client&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/observatory&#x22;" title="&#x22;observatory&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/hooks&#x22;" title="&#x22;hooks&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/semantic&#x22;" title="&#x22;semantic&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/compose&#x22;" title="&#x22;compose&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery&#x22;" title="&#x22;discovery&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/base&#x22;" title="&#x22;base&#x22;" />
    </Cards>
  </Tab>
</Tabs>
