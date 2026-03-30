# CapabilitySupport (/docs/python-reference/core/phlo/capabilities/support/CapabilitySupport)



Describe concrete guarantees a provider supports.

These flags let providers advertise optional behavior without forcing
every implementation to fake advanced semantics.

Attributes [#attributes]

<PyAttribute name="&#x22;supports_refs&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

<PyAttribute name="&#x22;supports_snapshots&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

<PyAttribute name="&#x22;supports_schema_evolution&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

<PyAttribute name="&#x22;supports_atomic_validation&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

<PyAttribute name="&#x22;supports_promote&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

<PyAttribute name="&#x22;supports_time_travel&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

<PyAttribute name="&#x22;supports_metrics&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

<PyAttribute name="&#x22;supports_logs&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

<PyAttribute name="&#x22;supports_dashboards&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

<PyAttribute name="&#x22;supports_alerts&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

<PyAttribute name="&#x22;supports_permissions&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

<PyAttribute name="&#x22;supports_attributes&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;to_dict&#x22;" type="&#x22;(self) -> dict[str, bool]&#x22;">
  Return the support metadata as a plain dictionary.

  <PySourceCode>
    ```python
    def to_dict(self) -> dict[str, bool]:
        """Return the support metadata as a plain dictionary."""
        return asdict(self)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, bool]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, supports_refs=False, supports_snapshots=False, supports_schema_evolution=False, supports_atomic_validation=False, supports_promote=False, supports_time_travel=False, supports_metrics=False, supports_logs=False, supports_dashboards=False, supports_alerts=False, supports_permissions=False, supports_attributes=False) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;supports_refs&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

    <PyParameter name="&#x22;supports_snapshots&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

    <PyParameter name="&#x22;supports_schema_evolution&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

    <PyParameter name="&#x22;supports_atomic_validation&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

    <PyParameter name="&#x22;supports_promote&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

    <PyParameter name="&#x22;supports_time_travel&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

    <PyParameter name="&#x22;supports_metrics&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

    <PyParameter name="&#x22;supports_logs&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

    <PyParameter name="&#x22;supports_dashboards&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

    <PyParameter name="&#x22;supports_alerts&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

    <PyParameter name="&#x22;supports_permissions&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />

    <PyParameter name="&#x22;supports_attributes&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
