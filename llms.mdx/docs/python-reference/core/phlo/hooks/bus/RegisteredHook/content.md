# RegisteredHook (/docs/python-reference/core/phlo/hooks/bus/RegisteredHook)



Internal record for a registered hook handler.

Attributes [#attributes]

<PyAttribute name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;hook_name&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;handler&#x22;" type="&#x22;Callable[[HookEvent], None] | Callable[[HookEvent], Awaitable[None]] | HookHandler | AsyncHookHandler&#x22;" value="null" />

<PyAttribute name="&#x22;priority&#x22;" type="&#x22;int&#x22;" value="null" />

<PyAttribute name="&#x22;filters&#x22;" type="&#x22;HookFilter | None&#x22;" value="null" />

<PyAttribute name="&#x22;failure_policy&#x22;" type="&#x22;FailurePolicy&#x22;" value="null" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, plugin_name, hook_name, handler, priority, filters, failure_policy) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;hook_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;handler&#x22;" type="&#x22;Callable[[HookEvent], None] | Callable[[HookEvent], Awaitable[None]] | HookHandler | AsyncHookHandler&#x22;" value="null" />

    <PyParameter name="&#x22;priority&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;filters&#x22;" type="&#x22;HookFilter | None&#x22;" value="null" />

    <PyParameter name="&#x22;failure_policy&#x22;" type="&#x22;FailurePolicy&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
