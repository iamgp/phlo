# HookProvider (/docs/python-reference/core/phlo/plugins/hooks/HookProvider)



Protocol for plugins that expose hook registrations.

Functions [#functions]

<PyFunction name="&#x22;get_hooks&#x22;" type="&#x22;(self) -> Iterable[HookRegistration]&#x22;">
  Return hook registrations exposed by the implementing plugin.

  <PySourceCode>
    ```python
    def get_hooks(self) -> Iterable[HookRegistration]:
        """Return hook registrations exposed by the implementing plugin.

        Returns:
            Iterable of hook registration definitions.
        """

        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable&#x22;">
    Iterable of hook registration definitions.
  </PyFunctionReturn>
</PyFunction>
