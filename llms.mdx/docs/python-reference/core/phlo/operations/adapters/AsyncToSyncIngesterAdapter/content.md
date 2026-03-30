# AsyncToSyncIngesterAdapter (/docs/python-reference/core/phlo/operations/adapters/AsyncToSyncIngesterAdapter)



Expose an async ingester behind the sync ingestion contract.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, ingester)&#x22;">
  <PySourceCode>
    ```python
    def __init__(self, ingester: AsyncIngester):
        super().__init__(context=ingester.context, logger=ingester.logger)
        self._ingester = ingester
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;ingester&#x22;" type="&#x22;AsyncIngester&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;run_ingestion&#x22;" type="&#x22;(self, partition_key, parameters) -> IngestionResult&#x22;">
  <PySourceCode>
    ```python
    def run_ingestion(
        self,
        partition_key: str | None,
        parameters: dict[str, Any],
    ) -> IngestionResult:
        _ensure_no_running_event_loop()
        return asyncio.run(self._ingester.run_ingestion(partition_key, parameters))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="null" />

    <PyParameter name="&#x22;parameters&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.operations.ingestion.IngestionResult&#x22;" />
</PyFunction>
