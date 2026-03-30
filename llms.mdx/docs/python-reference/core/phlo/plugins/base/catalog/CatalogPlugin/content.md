# CatalogPlugin (/docs/python-reference/core/phlo/plugins/base/catalog/CatalogPlugin)



Base class for engine-agnostic catalog plugins.

Catalog plugins define logical catalog configuration that engine adapters
serialize into their native formats (files or programmatic config).

Example:

```python
class ExampleCatalogPlugin(CatalogPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="example",
            version="1.0.0",
            description="Example catalog plugin",
        )

    @property
    def targets(self) -> list[str]:
        return ["engine-a", "engine-b"]

    @property
    def catalog_name(self) -> str:
        return "example"

    def get_properties(self) -> dict[str, str]:
        return \{
            "catalog.type": "example",
            "catalog.uri": "http://catalog:1234",
        \}
```

Attributes [#attributes]

<PyAttribute name="&#x22;targets&#x22;" type="&#x22;list[str]&#x22;" value="null">
  Return engine identifiers that can consume this catalog.

  Examples: \["trino"], \["spark"], \["trino", "spark"].
</PyAttribute>

<PyAttribute name="&#x22;catalog_name&#x22;" type="&#x22;str&#x22;" value="null">
  Return the catalog name.

  This becomes the catalog identifier in the engine.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_properties&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Return catalog configuration as key-value pairs.

  <PySourceCode>
    ```python
    @abstractmethod
    def get_properties(self) -> dict[str, Any]:
        """Return catalog configuration as key-value pairs.

        Returns:
            Dictionary of config key -> value

        """
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary of config key -> value
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;supports_target&#x22;" type="&#x22;(self, target) -> bool&#x22;">
  Return True if the catalog supports the requested engine target.

  <PySourceCode>
    ```python
    def supports_target(self, target: str) -> bool:
        """Return True if the catalog supports the requested engine target."""
        return target in self.targets
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>
