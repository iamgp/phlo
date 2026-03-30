# HookFilter (/docs/python-reference/core/phlo/plugins/hooks/HookFilter)



Filter criteria for deciding whether a hook should run.

Attributes [#attributes]

<PyAttribute name="&#x22;event_types&#x22;" type="&#x22;set[str] | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;asset_keys&#x22;" type="&#x22;set[str] | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;tags&#x22;" type="&#x22;dict[str, str] | None&#x22;" value="&#x22;None&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__post_init__&#x22;" type="&#x22;(self) -> None&#x22;">
  Normalize iterable fields to sets for efficient matching.

  <PySourceCode>
    ```python
    def __post_init__(self) -> None:
        """Normalize iterable fields to sets for efficient matching."""

        if self.event_types is not None:
            object.__setattr__(self, "event_types", set(self.event_types))
        if self.asset_keys is not None:
            object.__setattr__(self, "asset_keys", set(self.asset_keys))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, event_types=None, asset_keys=None, tags=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event_types&#x22;" type="&#x22;set[str] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;asset_keys&#x22;" type="&#x22;set[str] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
