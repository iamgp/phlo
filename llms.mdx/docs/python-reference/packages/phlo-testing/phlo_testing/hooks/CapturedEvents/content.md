# CapturedEvents (/docs/python-reference/packages/phlo-testing/phlo_testing/hooks/CapturedEvents)



Capture hook events in memory for assertions.

A container for collecting hook events emitted during test execution,
enabling verification of event sequences and properties.

Attributes [#attributes]

<PyAttribute name="&#x22;events&#x22;" type="&#x22;list[HookEvent]&#x22;" value="null">
  List of captured HookEvent instances.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;handler&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Append a hook event to the captured list.

  <PySourceCode>
    ```python
    def handler(self, event: HookEvent) -> None:
        """Append a hook event to the captured list.

        Args:
            event: The HookEvent instance to append to the capture list.

        """
        self.events.append(event)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;HookEvent&#x22;" value="undefined">
      The HookEvent instance to append to the capture list.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, events) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;events&#x22;" type="&#x22;list[HookEvent]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
