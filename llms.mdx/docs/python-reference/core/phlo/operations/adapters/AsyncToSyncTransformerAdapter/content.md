# AsyncToSyncTransformerAdapter (/docs/python-reference/core/phlo/operations/adapters/AsyncToSyncTransformerAdapter)



Expose an async transformer behind the sync transform contract.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, transformer)&#x22;">
  <PySourceCode>
    ```python
    def __init__(self, transformer: AsyncTransformer[Any]):
        super().__init__(context=transformer.context, logger=transformer.logger)
        self._transformer = transformer
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;transformer&#x22;" type="&#x22;AsyncTransformer[Any]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;run_transform&#x22;" type="&#x22;(self, partition_key=None, parameters=None) -> TransformationResult&#x22;">
  <PySourceCode>
    ```python
    def run_transform(
        self,
        partition_key: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> TransformationResult:
        _ensure_no_running_event_loop()
        return asyncio.run(self._transformer.run_transform(partition_key, parameters))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;parameters&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.operations.transformation.TransformationResult&#x22;" />
</PyFunction>
