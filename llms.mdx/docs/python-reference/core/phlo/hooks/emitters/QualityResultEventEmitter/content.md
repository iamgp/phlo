# QualityResultEventEmitter (/docs/python-reference/core/phlo/hooks/emitters/QualityResultEventEmitter)



Emit quality result events with a shared context.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, context, hook_bus=None) -> None&#x22;">
  Initialize the quality result event emitter.

  <PySourceCode>
    ```python
    def __init__(
        self,
        context: QualityResultEventContext,
        hook_bus: HookBus | None = None,
    ) -> None:
        """Initialize the quality result event emitter.

        Args:
            context: Shared quality-result context to include in each emitted event.
            hook_bus: Hook bus used to publish events. Defaults to the global bus.

        """
        self._context = context
        self._hook_bus = hook_bus or get_hook_bus()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;QualityResultEventContext&#x22;" value="undefined">
      Shared quality-result context to include in each emitted event.
    </PyParameter>

    <PyParameter name="&#x22;hook_bus&#x22;" type="&#x22;HookBus | None&#x22;" value="&#x22;None&#x22;">
      Hook bus used to publish events. Defaults to the global bus.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;emit_result&#x22;" type="&#x22;(self, *, check_name, passed, severity=None, check_type=None, metadata=None) -> None&#x22;">
  Emit a quality result event.

  <PySourceCode>
    ```python
    def emit_result(
        self,
        *,
        check_name: str,
        passed: bool,
        severity: str | None = None,
        check_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Emit a quality result event."""
        self._hook_bus.emit(
            QualityResultEvent(
                event_type="quality.result",
                asset_key=self._context.asset_key,
                check_name=check_name,
                passed=passed,
                severity=severity,
                check_type=check_type,
                partition_key=self._context.partition_key,
                metadata=metadata or {},
                tags=self._context.tags.copy(),
                correlation=_merge_correlation(
                    base=self._context.correlation,
                    overrides={
                        "run_id": self._context.run_id,
                        "asset_key": self._context.asset_key,
                        "partition_key": self._context.partition_key,
                        "check_name": check_name,
                    },
                ),
            )
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;check_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;passed&#x22;" type="&#x22;bool&#x22;" value="null" />

    <PyParameter name="&#x22;severity&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;check_type&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
