# BaseIngester (/docs/python-reference/core/phlo/operations/ingestion/BaseIngester)



Abstract base class for Phlo Ingestion Engines.

This ensures that different ingestion backends (DLT, Airbyte, Custom)
adhere to a common contract that Orchestrators (Dagster, Airflow) can consume.

Attributes [#attributes]

<PyAttribute name="&#x22;context&#x22;" type="null" value="&#x22;context&#x22;" />

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;logger&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, context, logger)&#x22;">
  Store runtime context and logger for ingestion implementations.

  <PySourceCode>
    ```python
    def __init__(self, context: Any, logger: Any):
        """Store runtime context and logger for ingestion implementations.

        Args:
            context: Orchestrator-provided execution context.
            logger: Logger used for ingestion diagnostics.
        """

        self.context = context
        self.logger = logger
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Orchestrator-provided execution context.
    </PyParameter>

    <PyParameter name="&#x22;logger&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Logger used for ingestion diagnostics.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;run_ingestion&#x22;" type="&#x22;(self, partition_key, parameters) -> IngestionResult&#x22;">
  Execute the ingestion logic for a specific partition.

  partition\_key may be None for unpartitioned runs.

  <PySourceCode>
    ```python
    @abstractmethod
    def run_ingestion(
        self, partition_key: str | None, parameters: dict[str, Any]
    ) -> IngestionResult:
        """
        Execute the ingestion logic for a specific partition.

        partition_key may be None for unpartitioned runs.
        """
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="null" />

    <PyParameter name="&#x22;parameters&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.operations.ingestion.IngestionResult&#x22;" />
</PyFunction>
