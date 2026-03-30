# QualityCheckResult (/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks/QualityCheckResult)



Result from executing a quality check.

This dataclass encapsulates the outcome of a quality check execution,
including pass/fail status, metric values, and detailed metadata for
debugging and observability.

Attributes [#attributes]

<PyAttribute name="&#x22;passed&#x22;" type="&#x22;bool&#x22;" value="null">
  Whether the quality check passed validation.
</PyAttribute>

<PyAttribute name="&#x22;metric_name&#x22;" type="&#x22;str&#x22;" value="null">
  Name of the quality metric being checked.
</PyAttribute>

<PyAttribute name="&#x22;metric_value&#x22;" type="&#x22;MetricValue&#x22;" value="null">
  Value of the quality metric (int, float, dict, or None).
</PyAttribute>

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;Metadata&#x22;" value="&#x22;field(default_factory=dict)&#x22;">
  Additional metadata about the check execution (default: empty dict).
</PyAttribute>

<PyAttribute name="&#x22;failure_message&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Human-readable failure message if check failed (default: None).
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, passed, metric_name, metric_value, metadata=dict(), failure_message=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;passed&#x22;" type="&#x22;bool&#x22;" value="null" />

    <PyParameter name="&#x22;metric_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;metric_value&#x22;" type="&#x22;MetricValue&#x22;" value="null" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;Metadata&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;failure_message&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
