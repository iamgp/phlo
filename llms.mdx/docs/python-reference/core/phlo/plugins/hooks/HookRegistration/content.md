# HookRegistration (/docs/python-reference/core/phlo/plugins/hooks/HookRegistration)



Registration details for a hook handler.

Attributes [#attributes]

<PyAttribute name="&#x22;hook_name&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;handler&#x22;" type="&#x22;Callable[[HookEvent], None] | Callable[[HookEvent], Awaitable[None]] | HookHandler | AsyncHookHandler&#x22;" value="null" />

<PyAttribute name="&#x22;priority&#x22;" type="&#x22;int&#x22;" value="&#x22;100&#x22;" />

<PyAttribute name="&#x22;filters&#x22;" type="&#x22;HookFilter | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;failure_policy&#x22;" type="&#x22;FailurePolicy&#x22;" value="&#x22;FailurePolicy.LOG&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, hook_name, handler, priority=100, filters=None, failure_policy=FailurePolicy.LOG) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;hook_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;handler&#x22;" type="&#x22;Callable[[HookEvent], None] | Callable[[HookEvent], Awaitable[None]] | HookHandler | AsyncHookHandler&#x22;" value="null" />

    <PyParameter name="&#x22;priority&#x22;" type="&#x22;int&#x22;" value="&#x22;100&#x22;" />

    <PyParameter name="&#x22;filters&#x22;" type="&#x22;HookFilter | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;failure_policy&#x22;" type="&#x22;FailurePolicy&#x22;" value="&#x22;FailurePolicy.LOG&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
