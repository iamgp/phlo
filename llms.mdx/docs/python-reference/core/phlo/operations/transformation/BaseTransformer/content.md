# BaseTransformer (/docs/python-reference/core/phlo/operations/transformation/BaseTransformer)



Base contract for transformation engines.

Attributes [#attributes]

<PyAttribute name="&#x22;context&#x22;" type="null" value="&#x22;context&#x22;" />

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;logger&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, context, logger)&#x22;">
  Initialize a transformer.

  <PySourceCode>
    ```python
    def __init__(self, context: ContextT, logger: Logger):
        """Initialize a transformer.

        Args:
            context: Engine-specific execution context.
            logger: Logger used for execution output.
        """
        self.context = context
        self.logger = logger
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;ContextT&#x22;" value="undefined">
      Engine-specific execution context.
    </PyParameter>

    <PyParameter name="&#x22;logger&#x22;" type="&#x22;Logger&#x22;" value="undefined">
      Logger used for execution output.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;run_transform&#x22;" type="&#x22;(self, partition_key=None, parameters=None) -> TransformationResult&#x22;">
  Run transformations for an optional partition.

  <PySourceCode>
    ```python
    @abstractmethod
    def run_transform(
        self,
        partition_key: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> TransformationResult:
        """Run transformations for an optional partition.

        Args:
            partition_key: Partition key for partition-scoped runs.
            parameters: Backend-specific runtime parameters.

        Returns:
            Transformation execution result metadata.
        """
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Partition key for partition-scoped runs.
    </PyParameter>

    <PyParameter name="&#x22;parameters&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Backend-specific runtime parameters.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo.operations.transformation.TransformationResult&#x22;">
    Transformation execution result metadata.
  </PyFunctionReturn>
</PyFunction>
