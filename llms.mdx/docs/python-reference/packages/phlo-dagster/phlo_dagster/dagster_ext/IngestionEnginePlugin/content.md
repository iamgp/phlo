# IngestionEnginePlugin (/docs/python-reference/packages/phlo-dagster/phlo_dagster/dagster_ext/IngestionEnginePlugin)



Base class for ingestion engine capability plugins.

Deprecated in favor of capability specs + orchestrator adapters.

Functions [#functions]

<PyFunction name="&#x22;__init_subclass__&#x22;" type="&#x22;(cls, **kwargs) -> None&#x22;">
  Warn on subclassing to signal deprecation.

  <PySourceCode>
    ```python
    def __init_subclass__(cls, **kwargs: object) -> None:
        """Warn on subclassing to signal deprecation.

        Args:
            **kwargs: Keyword arguments forwarded to type.__init_subclass__.

        Returns:
            None

        Raises:
            No explicit exceptions raised.

        """
        super().__init_subclass__(**kwargs)
        warnings.warn(
            "IngestionEnginePlugin is deprecated; use capability specs instead.",
            DeprecationWarning,
            stacklevel=2,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;kwargs&#x22;" type="&#x22;object&#x22;" value="&#x22;{}&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_ingestion_assets&#x22;" type="&#x22;(self) -> Iterable[Any]&#x22;">
  Return Dagster assets created by the ingestion engine.

  <PySourceCode>
    ```python
    @abstractmethod
    def get_ingestion_assets(self) -> Iterable[Any]:
        """Return Dagster assets created by the ingestion engine."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Iterable[typing.Any]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_ingestion_decorator&#x22;" type="&#x22;(self) -> Callable[..., Any]&#x22;">
  Return the decorator used to define ingestion assets.

  <PySourceCode>
    ```python
    @abstractmethod
    def get_ingestion_decorator(self) -> Callable[..., Any]:
        """Return the decorator used to define ingestion assets."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Callable[..., typing.Any]&#x22;" />
</PyFunction>
