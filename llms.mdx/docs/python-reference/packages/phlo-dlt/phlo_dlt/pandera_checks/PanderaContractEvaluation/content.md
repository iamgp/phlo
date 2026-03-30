# PanderaContractEvaluation (/docs/python-reference/packages/phlo-dlt/phlo_dlt/pandera_checks/PanderaContractEvaluation)



Result summary for Pandera schema contract evaluation.

This dataclass captures the outcome of validating data against a Pandera
schema, including pass/fail status, counts of failed/total records,
sample failure cases, and any error messages.

Attributes [#attributes]

<PyAttribute name="&#x22;passed&#x22;" type="&#x22;bool&#x22;" value="null">
  Whether validation passed (True) or failed (False).
</PyAttribute>

<PyAttribute name="&#x22;failed_count&#x22;" type="&#x22;int&#x22;" value="null">
  Number of records that failed validation.
</PyAttribute>

<PyAttribute name="&#x22;total_count&#x22;" type="&#x22;int&#x22;" value="null">
  Total number of records evaluated.
</PyAttribute>

<PyAttribute name="&#x22;sample&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="null">
  List of dicts containing up to 20 sample failure cases.
</PyAttribute>

<PyAttribute name="&#x22;error&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Error message if validation raised an exception, else None.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, passed, failed_count, total_count, sample, error=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;passed&#x22;" type="&#x22;bool&#x22;" value="null" />

    <PyParameter name="&#x22;failed_count&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;total_count&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;sample&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="null" />

    <PyParameter name="&#x22;error&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
