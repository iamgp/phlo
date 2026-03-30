# ServiceLifecycleEventEmitter (/docs/python-reference/core/phlo/hooks/emitters/ServiceLifecycleEventEmitter)



Emit service lifecycle events with a shared context.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, context, hook_bus=None) -> None&#x22;">
  Initialize the service lifecycle event emitter.

  <PySourceCode>
    ```python
    def __init__(
        self, context: ServiceLifecycleEventContext, hook_bus: HookBus | None = None
    ) -> None:
        """Initialize the service lifecycle event emitter.

        Args:
            context: Shared service context to include in each emitted event.
            hook_bus: Hook bus used to publish events. Defaults to the global bus.

        """
        self._context = context
        self._hook_bus = hook_bus or get_hook_bus()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;ServiceLifecycleEventContext&#x22;" value="undefined">
      Shared service context to include in each emitted event.
    </PyParameter>

    <PyParameter name="&#x22;hook_bus&#x22;" type="&#x22;HookBus | None&#x22;" value="&#x22;None&#x22;">
      Hook bus used to publish events. Defaults to the global bus.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;emit&#x22;" type="&#x22;(self, *, phase, status=None, metadata=None) -> None&#x22;">
  Emit a service lifecycle event for the given phase.

  <PySourceCode>
    ```python
    def emit(
        self,
        *,
        phase: str,
        status: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Emit a service lifecycle event for the given phase."""
        tags = self._context.tags.copy()
        tags["service"] = self._context.service_name
        tags["phase"] = phase
        self._hook_bus.emit(
            ServiceLifecycleEvent(
                event_type=f"service.{phase}",
                service_name=self._context.service_name,
                project_name=self._context.project_name,
                project_root=self._context.project_root,
                container_name=self._context.container_name,
                phase=phase,
                status=status,
                metadata=metadata or {},
                tags=tags,
                correlation=_merge_correlation(base=self._context.correlation),
            )
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;phase&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
