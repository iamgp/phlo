# contracts (/docs/python-reference/core/phlo/contracts)



Contract metadata models shared across ingestion and quality APIs.

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['Consumer', 'SLA', 'normalize_consumers', 'serialize_consumers', 'serialize_sla']&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;SLA&#x22;" href="&#x22;/docs/python-reference/core/phlo/contracts/SLA&#x22;" />

      <Card title="&#x22;Consumer&#x22;" href="&#x22;/docs/python-reference/core/phlo/contracts/Consumer&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;normalize_consumers&#x22;" type="&#x22;(consumers) -> list[Consumer]&#x22;">
      Normalize string and Consumer inputs into a Consumer list.

      <PySourceCode>
        ```python
        def normalize_consumers(consumers: list[Consumer | str] | None) -> list[Consumer]:
            """Normalize string and Consumer inputs into a Consumer list."""
            if not consumers:
                return []

            normalized: list[Consumer] = []
            for consumer in consumers:
                if isinstance(consumer, Consumer):
                    normalized.append(consumer)
                    continue
                normalized.append(Consumer(name=str(consumer)))
            return normalized
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;consumers&#x22;" type="&#x22;list[Consumer | str] | None&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;list[phlo.contracts.Consumer]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;serialize_consumers&#x22;" type="&#x22;(consumers) -> list[dict[str, Any]]&#x22;">
      Serialize consumers for capability metadata payloads.

      <PySourceCode>
        ```python
        def serialize_consumers(consumers: list[Consumer]) -> list[dict[str, Any]]:
            """Serialize consumers for capability metadata payloads."""
            return [asdict(consumer) for consumer in consumers]
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;consumers&#x22;" type="&#x22;list[Consumer]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;list[dict[str, typing.Any]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;serialize_sla&#x22;" type="&#x22;(sla) -> dict[str, Any] | None&#x22;">
      Serialize SLA for capability metadata payloads.

      <PySourceCode>
        ```python
        def serialize_sla(sla: SLA | None) -> dict[str, Any] | None:
            """Serialize SLA for capability metadata payloads."""
            if sla is None:
                return None
            return asdict(sla)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;sla&#x22;" type="&#x22;SLA | None&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any] | None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
