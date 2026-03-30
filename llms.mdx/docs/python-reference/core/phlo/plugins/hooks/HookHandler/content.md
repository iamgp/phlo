# HookHandler (/docs/python-reference/core/phlo/plugins/hooks/HookHandler)



Protocol for handler objects implementing hook dispatch.

Functions [#functions]

<PyFunction name="&#x22;handle_event&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Handle a hook event emitted by the hook bus.

  <PySourceCode>
    ```python
    def handle_event(self, event: HookEvent) -> None:
        """Handle a hook event emitted by the hook bus.

        Args:
            event: Hook event payload to process.
        """

        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;HookEvent&#x22;" value="undefined">
      Hook event payload to process.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
