# OrchestratorAdapterPlugin (/docs/python-reference/core/phlo/plugins/base/orchestrator/OrchestratorAdapterPlugin)



Base class for orchestrator adapters.

Functions [#functions]

<PyFunction name="&#x22;exec_service_name&#x22;" type="&#x22;(self) -> str | None&#x22;">
  Return the primary service name for container-based CLI execution.

  Adapters that expose a long-running service container users can exec into
  should override this method. Adapters without a corresponding container
  can return `None` and callers should fall back to host execution.

  <PySourceCode>
    ```python
    def exec_service_name(self) -> str | None:
        """Return the primary service name for container-based CLI execution.

        Adapters that expose a long-running service container users can exec into
        should override this method. Adapters without a corresponding container
        can return ``None`` and callers should fall back to host execution.
        """
        return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;build_definitions&#x22;" type="&#x22;(self, *, assets, checks, resources) -> Any&#x22;">
  Build orchestrator definitions from normalized capability specs.

  <PySourceCode>
    ```python
    @abstractmethod
    def build_definitions(
        self,
        *,
        assets: Iterable[AssetSpec],
        checks: Iterable[AssetCheckSpec],
        resources: Iterable[ResourceSpec],
    ) -> Any:
        """Build orchestrator definitions from normalized capability specs.

        Args:
            assets: Asset specifications to register.
            checks: Asset-check specifications to register.
            resources: Resource specifications required by assets/checks.

        Returns:
            Orchestrator-native definitions object.

        """
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;assets&#x22;" type="&#x22;Iterable[AssetSpec]&#x22;" value="undefined">
      Asset specifications to register.
    </PyParameter>

    <PyParameter name="&#x22;checks&#x22;" type="&#x22;Iterable[AssetCheckSpec]&#x22;" value="undefined">
      Asset-check specifications to register.
    </PyParameter>

    <PyParameter name="&#x22;resources&#x22;" type="&#x22;Iterable[ResourceSpec]&#x22;" value="undefined">
      Resource specifications required by assets/checks.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Orchestrator-native definitions object.
  </PyFunctionReturn>
</PyFunction>
