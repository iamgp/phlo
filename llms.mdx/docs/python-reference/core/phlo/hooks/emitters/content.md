# emitters (/docs/python-reference/core/phlo/hooks/emitters)



Helper emitters for publishing hook events.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;IngestionEventContext&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/IngestionEventContext&#x22;" />

      <Card title="&#x22;IngestionEventEmitter&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/IngestionEventEmitter&#x22;" />

      <Card title="&#x22;TransformEventContext&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/TransformEventContext&#x22;" />

      <Card title="&#x22;TransformEventEmitter&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/TransformEventEmitter&#x22;" />

      <Card title="&#x22;PublishEventContext&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/PublishEventContext&#x22;" />

      <Card title="&#x22;PublishEventEmitter&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/PublishEventEmitter&#x22;" />

      <Card title="&#x22;QualityResultEventContext&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/QualityResultEventContext&#x22;" />

      <Card title="&#x22;QualityResultEventEmitter&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/QualityResultEventEmitter&#x22;" />

      <Card title="&#x22;LineageEventContext&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/LineageEventContext&#x22;" />

      <Card title="&#x22;LineageEventEmitter&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/LineageEventEmitter&#x22;" />

      <Card title="&#x22;TelemetryEventContext&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/TelemetryEventContext&#x22;" />

      <Card title="&#x22;TelemetryEventEmitter&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/TelemetryEventEmitter&#x22;" />

      <Card title="&#x22;ServiceLifecycleEventContext&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/ServiceLifecycleEventContext&#x22;" />

      <Card title="&#x22;ServiceLifecycleEventEmitter&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/ServiceLifecycleEventEmitter&#x22;" />

      <Card title="&#x22;SchemaMigrationEventContext&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/SchemaMigrationEventContext&#x22;" />

      <Card title="&#x22;SchemaMigrationEventEmitter&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/SchemaMigrationEventEmitter&#x22;" />

      <Card title="&#x22;DataMigrationEventContext&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/DataMigrationEventContext&#x22;" />

      <Card title="&#x22;DataMigrationEventEmitter&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/emitters/DataMigrationEventEmitter&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_merge_correlation&#x22;" type="&#x22;(*, base=None, overrides=None) -> HookCorrelation&#x22;">
      Merge bound, explicit, and event-specific correlation fields.

      <PySourceCode>
        ```python
        def _merge_correlation(
            *,
            base: HookCorrelation | None = None,
            overrides: dict[str, Any] | None = None,
        ) -> HookCorrelation:
            """Merge bound, explicit, and event-specific correlation fields."""
            correlation = HookCorrelation(**vars(get_bound_correlation_context()))
            if base is not None:
                for key, value in vars(base).items():
                    if value is not None:
                        setattr(correlation, key, str(value))
            if overrides is not None:
                for key, value in overrides.items():
                    if value is not None:
                        setattr(correlation, key, str(value))
            return correlation
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;base&#x22;" type="&#x22;HookCorrelation | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;overrides&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.hooks.events.HookCorrelation&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
