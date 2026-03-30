# AssetProviderPlugin (/docs/python-reference/core/phlo/plugins/base/providers/AssetProviderPlugin)



Base class for capability plugins that provide asset specs.

Attributes [#attributes]

<PyAttribute name="&#x22;requires_capabilities&#x22;" type="&#x22;list[str]&#x22;" value="null">
  Return required capabilities for this provider.
</PyAttribute>

<PyAttribute name="&#x22;optional_capabilities&#x22;" type="&#x22;list[str]&#x22;" value="null">
  Return optional capabilities for this provider.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_assets&#x22;" type="&#x22;(self) -> Iterable[AssetSpec]&#x22;">
  Return asset specifications exposed by this plugin.

  <PySourceCode>
    ```python
    @abstractmethod
    def get_assets(self) -> Iterable[AssetSpec]:
        """Return asset specifications exposed by this plugin.

        Returns:
            Iterable of asset specifications.

        """
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable&#x22;">
    Iterable of asset specifications.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_checks&#x22;" type="&#x22;(self) -> Iterable[AssetCheckSpec]&#x22;">
  Return asset check specifications exposed by this plugin.

  <PySourceCode>
    ```python
    def get_checks(self) -> Iterable[AssetCheckSpec]:
        """Return asset check specifications exposed by this plugin.

        Returns:
            Iterable of asset check specifications.

        """
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable&#x22;">
    Iterable of asset check specifications.
  </PyFunctionReturn>
</PyFunction>
