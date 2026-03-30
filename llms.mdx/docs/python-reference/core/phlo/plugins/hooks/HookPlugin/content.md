# HookPlugin (/docs/python-reference/core/phlo/plugins/hooks/HookPlugin)



Base class for hook-only plugins.

Functions [#functions]

<PyFunction name="&#x22;get_hooks&#x22;" type="&#x22;(self) -> Iterable[HookRegistration]&#x22;">
  Return hook registrations for this plugin.

  <PySourceCode>
    ```python
    def get_hooks(self) -> Iterable[HookRegistration]:
        """Return hook registrations for this plugin."""

        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.plugins.hooks.HookRegistration]&#x22;" />
</PyFunction>
