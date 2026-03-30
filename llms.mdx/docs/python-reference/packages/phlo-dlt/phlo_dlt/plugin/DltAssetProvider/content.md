# DltAssetProvider (/docs/python-reference/packages/phlo-dlt/phlo_dlt/plugin/DltAssetProvider)



Provide DLT-defined ingestion assets and checks to Phlo.

Asset provider plugin that exposes all ingestion assets registered
via the `@phlo_ingestion` decorator. Discovered by Phlo's plugin
system and used during asset loading.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Static plugin metadata for discovery.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_assets&#x22;" type="&#x22;(self) -> Iterable[AssetSpec]&#x22;">
  Return registered DLT ingestion assets.

  <PySourceCode>
    ```python
    def get_assets(self) -> Iterable[AssetSpec]:
        """Return registered DLT ingestion assets.

        Returns:
            Iterable[AssetSpec]: Asset specifications discovered from DLT decorators.

        """
        return get_ingestion_assets()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable&#x22;">
    Iterable\[AssetSpec]: Asset specifications discovered from DLT decorators.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_checks&#x22;" type="&#x22;(self) -> Iterable[AssetCheckSpec]&#x22;">
  Return asset checks exposed by this provider.

  <PySourceCode>
    ```python
    def get_checks(self) -> Iterable[AssetCheckSpec]:
        """Return asset checks exposed by this provider.

        Returns:
            Iterable[AssetCheckSpec]: Empty iterable because DLT provider has no checks.
            Checks are attached to individual assets, not the provider.

        """
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable&#x22;">
    Iterable\[AssetCheckSpec]: Empty iterable because DLT provider has no checks.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;clear_registries&#x22;" type="&#x22;(self) -> None&#x22;">
  Clear in-memory DLT ingestion asset registrations.

  Removes all registered assets from the internal registry.
  Called during plugin reload or testing scenarios.

  <PySourceCode>
    ```python
    def clear_registries(self) -> None:
        """Clear in-memory DLT ingestion asset registrations.

        Removes all registered assets from the internal registry.
        Called during plugin reload or testing scenarios.

        """
        clear_ingestion_assets()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
