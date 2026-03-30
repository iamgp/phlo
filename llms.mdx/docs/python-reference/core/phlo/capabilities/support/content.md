# support (/docs/python-reference/core/phlo/capabilities/support)



Structured capability support metadata.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;CapabilitySupport&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/support/CapabilitySupport&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;coerce_capability_support&#x22;" type="&#x22;(value) -> CapabilitySupport&#x22;">
      Normalize raw support metadata into `CapabilitySupport`.

      <PySourceCode>
        ```python
        def coerce_capability_support(
            value: CapabilitySupport | Mapping[str, Any] | None,
        ) -> CapabilitySupport:
            """Normalize raw support metadata into ``CapabilitySupport``.

            Args:
                value: Existing support object, mapping payload, or ``None``.

            Returns:
                Normalized ``CapabilitySupport`` instance.
            """
            if isinstance(value, CapabilitySupport):
                return value
            if value is None:
                return CapabilitySupport()
            if isinstance(value, Mapping):
                allowed_keys = {
                    "supports_refs",
                    "supports_snapshots",
                    "supports_schema_evolution",
                    "supports_atomic_validation",
                    "supports_promote",
                    "supports_time_travel",
                    "supports_metrics",
                    "supports_logs",
                    "supports_dashboards",
                    "supports_alerts",
                    "supports_permissions",
                    "supports_attributes",
                }
                payload = {key: bool(raw_value) for key, raw_value in value.items() if key in allowed_keys}
                return CapabilitySupport(**payload)
            raise TypeError(f"Unsupported capability support payload: {type(value)!r}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;CapabilitySupport | Mapping[str, Any] | None&#x22;" value="undefined">
          Existing support object, mapping payload, or `None`.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo.capabilities.support.CapabilitySupport&#x22;">
        Normalized `CapabilitySupport` instance.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
