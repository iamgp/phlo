# SlingAssetProvider (/docs/python-reference/packages/phlo-sling/phlo_sling/plugin/SlingAssetProvider)



Provide Sling-defined replication assets and checks to Phlo.

This plugin class discovers and exposes Sling replication assets registered
via decorators to the Phlo orchestration runtime. It manages the lifecycle
of Sling asset registrations.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Information about this plugin including
  name, version, and description.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_assets&#x22;" type="&#x22;(self) -> Iterable[AssetSpec]&#x22;">
  Return registered Sling replication assets.

  Retrieves all Sling replication assets that have been registered
  via the @phlo\_sling\_replication or @phlo\_sling\_assets decorators.

  <PySourceCode>
    ```python
    def get_assets(self) -> Iterable[AssetSpec]:
        """Return registered Sling replication assets.

        Retrieves all Sling replication assets that have been registered
        via the @phlo_sling_replication or @phlo_sling_assets decorators.

        Returns:
            Iterable of AssetSpec objects representing registered
            Sling replication pipelines.

        """
        return get_sling_assets()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable&#x22;">
    Iterable of AssetSpec objects representing registered
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_checks&#x22;" type="&#x22;(self) -> Iterable[AssetCheckSpec]&#x22;">
  Return asset checks exposed by this provider.

  Currently, Sling replication assets do not expose any built-in
  asset checks through this provider.

  <PySourceCode>
    ```python
    def get_checks(self) -> Iterable[AssetCheckSpec]:
        """Return asset checks exposed by this provider.

        Currently, Sling replication assets do not expose any built-in
        asset checks through this provider.

        Returns:
            Empty iterable as no checks are defined.

        """
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable&#x22;">
    Empty iterable as no checks are defined.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;clear_registries&#x22;" type="&#x22;(self) -> None&#x22;">
  Clear in-memory Sling replication asset registrations.

  Removes all registered Sling assets from the internal registry.
  This is typically called during testing or plugin reload scenarios.

  <PySourceCode>
    ```python
    def clear_registries(self) -> None:
        """Clear in-memory Sling replication asset registrations.

        Removes all registered Sling assets from the internal registry.
        This is typically called during testing or plugin reload scenarios.

        Returns:
            None

        """
        clear_sling_assets()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>
