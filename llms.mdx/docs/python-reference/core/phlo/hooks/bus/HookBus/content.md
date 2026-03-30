# HookBus (/docs/python-reference/core/phlo/hooks/bus/HookBus)



Dispatch hook events to registered handlers.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self) -> None&#x22;">
  Initialize hook bus storage and lazy-discovery state.

  <PySourceCode>
    ```python
    def __init__(self) -> None:
        """Initialize hook bus storage and lazy-discovery state."""
        self._hooks: list[RegisteredHook] = []
        self._discovered = False
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;emit&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Emit an event to all matching hooks.

  <PySourceCode>
    ```python
    def emit(self, event: HookEvent) -> None:
        """Emit an event to all matching hooks."""
        self._ensure_discovered()
        for hook in sorted(
            self._hooks, key=lambda item: (item.priority, item.plugin_name, item.hook_name)
        ):
            if hook.filters and not self._matches_filters(hook.filters, event):
                continue
            try:
                self._invoke_handler(hook.handler, event)
            except TypeError:
                raise
            except Exception as exc:
                if self._handle_failure(hook=hook, error=exc):
                    continue
                raise
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;HookEvent&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;emit_async&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Emit an event asynchronously to all matching hooks.

  <PySourceCode>
    ```python
    async def emit_async(self, event: HookEvent) -> None:
        """Emit an event asynchronously to all matching hooks."""
        self._ensure_discovered()
        for hook in sorted(
            self._hooks, key=lambda item: (item.priority, item.plugin_name, item.hook_name)
        ):
            if hook.filters and not self._matches_filters(hook.filters, event):
                continue
            try:
                await self._invoke_handler_async(hook.handler, event)
            except TypeError:
                raise
            except Exception as exc:
                if self._handle_failure(hook=hook, error=exc):
                    continue
                raise
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;HookEvent&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register&#x22;" type="&#x22;(self, registration, *, plugin_name) -> None&#x22;">
  Register a hook handler.

  <PySourceCode>
    ```python
    def register(self, registration: HookRegistration, *, plugin_name: str) -> None:
        """Register a hook handler."""
        self._hooks.append(
            RegisteredHook(
                plugin_name=plugin_name,
                hook_name=registration.hook_name,
                handler=registration.handler,
                priority=registration.priority,
                filters=registration.filters,
                failure_policy=registration.failure_policy,
            )
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;registration&#x22;" type="&#x22;HookRegistration&#x22;" value="null" />

    <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_provider&#x22;" type="&#x22;(self, provider, *, plugin_name=None) -> None&#x22;">
  Register hooks from a provider.

  <PySourceCode>
    ```python
    def register_provider(self, provider: HookProvider, *, plugin_name: str | None = None) -> None:
        """Register hooks from a provider."""
        resolved_name = plugin_name or _resolve_plugin_name(provider) or "unknown"
        for hook in provider.get_hooks():
            self.register(hook, plugin_name=resolved_name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;provider&#x22;" type="&#x22;HookProvider&#x22;" value="null" />

    <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;clear&#x22;" type="&#x22;(self) -> None&#x22;">
  Remove all registered hooks.

  <PySourceCode>
    ```python
    def clear(self) -> None:
        """Remove all registered hooks."""
        self._hooks.clear()
        self._discovered = False
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_ensure_discovered&#x22;" type="&#x22;(self) -> None&#x22;">
  Discover plugins and register hook providers on first use.

  <PySourceCode>
    ```python
    def _ensure_discovered(self) -> None:
        """Discover plugins and register hook providers on first use."""
        if self._discovered:
            return
        from phlo.hooks.telemetry import CoreTelemetryHookProvider
        from phlo.plugins.discovery import discover_plugins, get_global_registry

        self.register_provider(CoreTelemetryHookProvider(), plugin_name="core")
        discover_plugins(auto_register=True)
        registry = get_global_registry()
        for plugin in registry.iter_plugins():
            if isinstance(plugin, HookProvider):
                self.register_provider(plugin)
        self._discovered = True
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_invoke_handler&#x22;" type="&#x22;(handler, event) -> None&#x22;">
  Dispatch a hook handler regardless of implementation style.

  <PySourceCode>
    ```python
    @staticmethod
    def _invoke_handler(
        handler: (
            Callable[[HookEvent], None]
            | Callable[[HookEvent], Awaitable[None]]
            | HookHandler
            | AsyncHookHandler
        ),
        event: HookEvent,
    ) -> None:
        """Dispatch a hook handler regardless of implementation style."""
        if isinstance(handler, AsyncHookHandler):
            raise TypeError(
                "Async hook handler requires HookBus.emit_async(). "
                "Use a sync handler or call emit_async for this event."
            )
        if isinstance(handler, HookHandler):
            handler.handle_event(event)
            return
        result = handler(event)
        if inspect.isawaitable(result):
            if inspect.iscoroutine(result):
                result.close()
            raise TypeError(
                "Async hook function requires HookBus.emit_async(). "
                "Use a sync handler or call emit_async for this event."
            )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;handler&#x22;" type="&#x22;Callable[[HookEvent], None] | Callable[[HookEvent], Awaitable[None]] | HookHandler | AsyncHookHandler&#x22;" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;HookEvent&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_invoke_handler_async&#x22;" type="&#x22;(handler, event) -> None&#x22;">
  Dispatch a hook handler from an async execution context.

  <PySourceCode>
    ```python
    @staticmethod
    async def _invoke_handler_async(
        handler: (
            Callable[[HookEvent], None]
            | Callable[[HookEvent], Awaitable[None]]
            | HookHandler
            | AsyncHookHandler
        ),
        event: HookEvent,
    ) -> None:
        """Dispatch a hook handler from an async execution context."""
        if isinstance(handler, AsyncHookHandler):
            await handler.handle_event_async(event)
            return
        if isinstance(handler, HookHandler):
            handler.handle_event(event)
            return
        result = handler(event)
        if inspect.isawaitable(result):
            await result
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;handler&#x22;" type="&#x22;Callable[[HookEvent], None] | Callable[[HookEvent], Awaitable[None]] | HookHandler | AsyncHookHandler&#x22;" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;HookEvent&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_handle_failure&#x22;" type="&#x22;(*, hook, error) -> bool&#x22;">
  Apply failure policy, returning True when dispatch should continue.

  <PySourceCode>
    ```python
    @staticmethod
    def _handle_failure(*, hook: RegisteredHook, error: Exception) -> bool:
        """Apply failure policy, returning True when dispatch should continue."""
        policy = hook.failure_policy
        if policy == FailurePolicy.IGNORE:
            return True
        if policy == FailurePolicy.LOG:
            logger.exception(
                "Hook failed: %s.%s (%s)",
                hook.plugin_name,
                hook.hook_name,
                error,
            )
            return True
        return False
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;hook&#x22;" type="&#x22;RegisteredHook&#x22;" value="null" />

    <PyParameter name="&#x22;error&#x22;" type="&#x22;Exception&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_matches_filters&#x22;" type="&#x22;(filters, event) -> bool&#x22;">
  Return whether an event satisfies the provided hook filters.

  <PySourceCode>
    ```python
    @staticmethod
    def _matches_filters(filters: HookFilter, event: HookEvent) -> bool:
        """Return whether an event satisfies the provided hook filters."""
        if filters.event_types and event.event_type not in filters.event_types:
            return False
        if filters.asset_keys:
            event_asset_keys = _event_asset_keys(event)
            if not event_asset_keys or not filters.asset_keys.intersection(event_asset_keys):
                return False
        return not (
            filters.tags and not all(event.tags.get(k) == v for k, v in filters.tags.items())
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;filters&#x22;" type="&#x22;HookFilter&#x22;" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;HookEvent&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>
