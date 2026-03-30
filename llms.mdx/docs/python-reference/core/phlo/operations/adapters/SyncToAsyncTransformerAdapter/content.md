# SyncToAsyncTransformerAdapter (/docs/python-reference/core/phlo/operations/adapters/SyncToAsyncTransformerAdapter)



Expose a sync transformer behind the async transform contract.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, transformer)&#x22;">
  <PySourceCode>
    ```python
    def __init__(self, transformer: BaseTransformer[Any]):
        super().__init__(context=transformer.context, logger=transformer.logger)
        self._transformer = transformer
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;transformer&#x22;" type="&#x22;BaseTransformer[Any]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;run_transform&#x22;" type="&#x22;(self, partition_key=None, parameters=None) -> TransformationResult&#x22;">
  <PySourceCode>
    ```python
    async def run_transform(
        self,
        partition_key: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> TransformationResult:
        return await asyncio.to_thread(self._transformer.run_transform, partition_key, parameters)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;parameters&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.operations.transformation.TransformationResult&#x22;" />
</PyFunction>
