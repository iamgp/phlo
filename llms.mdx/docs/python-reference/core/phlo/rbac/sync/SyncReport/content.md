# SyncReport (/docs/python-reference/core/phlo/rbac/sync/SyncReport)



Structured sync report as defined in Spec 0017.

Attributes [#attributes]

<PyAttribute name="&#x22;policy_version_hash&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;backend&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;environment&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;planned_count&#x22;" type="&#x22;int&#x22;" value="null" />

<PyAttribute name="&#x22;applied_count&#x22;" type="&#x22;int&#x22;" value="null" />

<PyAttribute name="&#x22;verification_result&#x22;" type="&#x22;bool | None&#x22;" value="null" />

<PyAttribute name="&#x22;drift_summary&#x22;" type="&#x22;dict[str, int]&#x22;" value="null" />

<PyAttribute name="&#x22;request_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;errors&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="&#x22;()&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;to_dict&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Convert report to dictionary.

  <PySourceCode>
    ```python
    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "policy_version_hash": self.policy_version_hash,
            "backend": self.backend,
            "environment": self.environment,
            "planned_count": self.planned_count,
            "applied_count": self.applied_count,
            "verification_result": self.verification_result,
            "drift_summary": self.drift_summary,
            "request_id": self.request_id,
            "errors": list(self.errors),
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, policy_version_hash, backend, environment, planned_count, applied_count, verification_result, drift_summary, request_id=None, errors=()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;policy_version_hash&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;backend&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;environment&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;planned_count&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;applied_count&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;verification_result&#x22;" type="&#x22;bool | None&#x22;" value="null" />

    <PyParameter name="&#x22;drift_summary&#x22;" type="&#x22;dict[str, int]&#x22;" value="null" />

    <PyParameter name="&#x22;request_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;errors&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="&#x22;()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
