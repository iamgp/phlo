# SemanticLayerProvider (/docs/python-reference/core/phlo/plugins/semantic/SemanticLayerProvider)



Base class for providers exposing semantic models.

Functions [#functions]

<PyFunction name="&#x22;list_models&#x22;" type="&#x22;(self) -> Iterable[SemanticModel]&#x22;">
  Return all semantic models exposed by this provider.

  <PySourceCode>
    ```python
    @abstractmethod
    def list_models(self) -> Iterable[SemanticModel]:
        """Return all semantic models exposed by this provider."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.plugins.semantic.SemanticModel]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_model&#x22;" type="&#x22;(self, name) -> SemanticModel | None&#x22;">
  Return a semantic model by name when present.

  <PySourceCode>
    ```python
    @abstractmethod
    def get_model(self, name: str) -> SemanticModel | None:
        """Return a semantic model by name when present."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.semantic.SemanticModel | None&#x22;" />
</PyFunction>
