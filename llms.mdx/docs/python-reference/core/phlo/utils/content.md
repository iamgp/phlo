# utils (/docs/python-reference/core/phlo/utils)



Common utility functions for Phlo.

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;compact_dict&#x22;" type="&#x22;(d) -> dict[str, Any]&#x22;">
      Remove None values from a dictionary.

      <PySourceCode>
        ```python
        def compact_dict(d: Mapping[str, Any]) -> dict[str, Any]:
            """Remove None values from a dictionary."""
            return {k: v for k, v in d.items() if v is not None}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;d&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;dedupe_preserve_order&#x22;" type="&#x22;(values) -> list[_T]&#x22;">
      Return unique values in input order.

      <PySourceCode>
        ```python
        def dedupe_preserve_order(values: Iterable[_T]) -> list[_T]:
            """Return unique values in input order."""
            seen: set[_T] = set()
            deduped: list[_T] = []
            for value in values:
                if value in seen:
                    continue
                seen.add(value)
                deduped.append(value)
            return deduped
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;values&#x22;" type="&#x22;Iterable[_T]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;list[phlo.utils._T]&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
