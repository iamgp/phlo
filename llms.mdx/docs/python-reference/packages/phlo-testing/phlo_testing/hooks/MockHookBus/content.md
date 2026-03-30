# MockHookBus (/docs/python-reference/packages/phlo-testing/phlo_testing/hooks/MockHookBus)



Hook bus that skips plugin discovery for tests.

A lightweight mock implementation of HookBus that bypasses plugin
discovery, allowing tests to register and emit events in isolation
without loading actual plugins.

Example:

> > > bus = MockHookBus()
> > > bus.register(HookRegistration(
> > > ...     hook\_name="test",
> > > ...     handler=lambda e: print(e),
> > > ... ))

Functions [#functions]

<PyFunction name="&#x22;_ensure_discovered&#x22;" type="&#x22;(self) -> None&#x22;">
  Override discovery to skip plugin loading.

  <PySourceCode>
    ```python
    def _ensure_discovered(self) -> None:
        """Override discovery to skip plugin loading."""
        self._discovered = True
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
