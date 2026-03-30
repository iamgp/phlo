# PanderaContractEvaluation (/docs/python-reference/packages/phlo-pandera/phlo_pandera/pandera_asset_checks/PanderaContractEvaluation)



Result summary for Pandera schema contract evaluation.

This dataclass encapsulates the outcome of validating a DataFrame against
a Pandera schema. It provides a standardized summary independent of Pandera's
internal error types.

Attributes [#attributes]

<PyAttribute name="&#x22;passed&#x22;" type="&#x22;bool&#x22;" value="null">
  Whether validation passed without contract failures.
</PyAttribute>

<PyAttribute name="&#x22;failed_count&#x22;" type="&#x22;int&#x22;" value="null">
  Number of failing rows or checks.
</PyAttribute>

<PyAttribute name="&#x22;total_count&#x22;" type="&#x22;int&#x22;" value="null">
  Total number of evaluated rows.
</PyAttribute>

<PyAttribute name="&#x22;sample&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="null">
  Sample failure payload for metadata and debugging.
</PyAttribute>

<PyAttribute name="&#x22;error&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Optional top-level validation error message for catastrophic failures.
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
