# PanderaContractValidationError (/docs/python-reference/packages/phlo-dlt/phlo_dlt/pandera_checks/PanderaContractValidationError)



Raised when strict Pandera validation fails before a visible write.

This exception is raised when strict validation is enabled and the
Pandera contract check fails. It includes the evaluation details and
paths to the Parquet files that failed validation.

Attributes [#attributes]

<PyAttribute name="&#x22;evaluation&#x22;" type="&#x22;PanderaContractEvaluation&#x22;" value="null">
  Detailed evaluation result with failure information.
</PyAttribute>

<PyAttribute name="&#x22;parquet_paths&#x22;" type="&#x22;tuple[Path, ...]&#x22;" value="null">
  Tuple of paths to the Parquet files that were validated.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__post_init__&#x22;" type="&#x22;(self) -> None&#x22;">
  Initialize the RuntimeError base class with a standard message.

  <PySourceCode>
    ```python
    def __post_init__(self) -> None:
        """Initialize the RuntimeError base class with a standard message."""
        RuntimeError.__init__(self, "Pandera contract validation failed")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, evaluation, parquet_paths) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;evaluation&#x22;" type="&#x22;PanderaContractEvaluation&#x22;" value="null" />

    <PyParameter name="&#x22;parquet_paths&#x22;" type="&#x22;tuple[Path, ...]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
