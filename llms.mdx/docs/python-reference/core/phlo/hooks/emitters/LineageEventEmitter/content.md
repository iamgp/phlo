# LineageEventEmitter (/docs/python-reference/core/phlo/hooks/emitters/LineageEventEmitter)



Emit lineage events with a shared context.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, context, hook_bus=None) -> None&#x22;">
  Initialize the lineage event emitter.

  <PySourceCode>
    ```python
    def __init__(self, context: LineageEventContext, hook_bus: HookBus | None = None) -> None:
        """Initialize the lineage event emitter.

        Args:
            context: Shared lineage context to include in each emitted event.
            hook_bus: Hook bus used to publish events. Defaults to the global bus.

        """
        self._context = context
        self._hook_bus = hook_bus or get_hook_bus()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;LineageEventContext&#x22;" value="undefined">
      Shared lineage context to include in each emitted event.
    </PyParameter>

    <PyParameter name="&#x22;hook_bus&#x22;" type="&#x22;HookBus | None&#x22;" value="&#x22;None&#x22;">
      Hook bus used to publish events. Defaults to the global bus.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;emit_edges&#x22;" type="&#x22;(self, *, edges, asset_keys=None, metadata=None) -> None&#x22;">
  Emit a lineage edges event.

  <PySourceCode>
    ```python
    def emit_edges(
        self,
        *,
        edges: list[tuple[str, str]],
        asset_keys: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Emit a lineage edges event."""
        self._hook_bus.emit(
            LineageEvent(
                event_type="lineage.edges",
                edges=list(edges),
                asset_keys=list(asset_keys) if asset_keys else [],
                metadata=metadata or {},
                tags=self._context.tags.copy(),
                correlation=_merge_correlation(base=self._context.correlation),
            )
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;edges&#x22;" type="&#x22;list[tuple[str, str]]&#x22;" value="null" />

    <PyParameter name="&#x22;asset_keys&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
