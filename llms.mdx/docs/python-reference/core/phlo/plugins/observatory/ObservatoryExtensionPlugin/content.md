# ObservatoryExtensionPlugin (/docs/python-reference/core/phlo/plugins/observatory/ObservatoryExtensionPlugin)



Base class for Observatory UI extension plugins.

Attributes [#attributes]

<PyAttribute name="&#x22;manifest&#x22;" type="&#x22;ObservatoryExtensionManifest | dict[str, Any]&#x22;" value="null">
  Return the extension manifest or a raw manifest dict.
</PyAttribute>

<PyAttribute name="&#x22;asset_root&#x22;" type="&#x22;Traversable&#x22;" value="null">
  Return the root directory that contains the extension assets.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_manifest&#x22;" type="&#x22;(self) -> ObservatoryExtensionManifest&#x22;">
  Return a validated manifest instance.

  <PySourceCode>
    ```python
    def get_manifest(self) -> ObservatoryExtensionManifest:
        """Return a validated manifest instance."""
        if isinstance(self.manifest, ObservatoryExtensionManifest):
            return self.manifest
        return ObservatoryExtensionManifest.model_validate(self.manifest)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.observatory.ObservatoryExtensionManifest&#x22;" />
</PyFunction>
