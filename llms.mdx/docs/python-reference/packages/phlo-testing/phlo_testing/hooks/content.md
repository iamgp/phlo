# hooks (/docs/python-reference/packages/phlo-testing/phlo_testing/hooks)



Hook testing utilities for Phlo workflows.

Provides mock implementations and helpers for testing the Phlo hook system,
including event capture, sample event generation, and mock hook bus for
isolated testing.

Example:

> > > from phlo\_testing.hooks import MockHookBus, capture\_events, sample\_ingestion\_event
> > > bus = MockHookBus()
> > > captured = capture\_events(bus=bus, event\_types=\["ingestion.end"])
> > > bus.emit(sample\_ingestion\_event())
> > > assert len(captured.events) == 1

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;MockHookBus&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/hooks/MockHookBus&#x22;" />

      <Card title="&#x22;CapturedEvents&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/hooks/CapturedEvents&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;capture_events&#x22;" type="&#x22;(*, bus, event_types=None) -> CapturedEvents&#x22;">
      Register a hook handler that collects emitted events.

      Creates and registers a capture handler on the provided hook bus,
      optionally filtered to specific event types.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > bus = MockHookBus()
        > > > captured = capture\_events(
        > > > ...     bus=bus,
        > > > ...     event\_types=\["ingestion.end", "quality.result"]
        > > > ... )
        > > > bus.emit(sample\_ingestion\_event())
        > > > assert len(captured.events) == 1
      </Callout>

      <PySourceCode>
        ```python
        def capture_events(
            *,
            bus: HookBus,
            event_types: Iterable[str] | None = None,
        ) -> CapturedEvents:
            """Register a hook handler that collects emitted events.

            Creates and registers a capture handler on the provided hook bus,
            optionally filtered to specific event types.

            Args:
                bus: The HookBus instance to register the capture handler on.
                event_types: Optional iterable of event type strings to filter.
                    If None, captures all event types.

            Returns:
                A CapturedEvents instance containing the collected events.

            Example:
                >>> bus = MockHookBus()
                >>> captured = capture_events(
                ...     bus=bus,
                ...     event_types=["ingestion.end", "quality.result"]
                ... )
                >>> bus.emit(sample_ingestion_event())
                >>> assert len(captured.events) == 1

            """
            captured = CapturedEvents(events=[])
            filters = HookFilter(event_types=set(event_types)) if event_types else None
            bus.register(
                HookRegistration(
                    hook_name="capture_events",
                    handler=captured.handler,
                    filters=filters,
                ),
                plugin_name="phlo-testing",
            )
            return captured
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;bus&#x22;" type="&#x22;HookBus&#x22;" value="undefined">
          The HookBus instance to register the capture handler on.
        </PyParameter>

        <PyParameter name="&#x22;event_types&#x22;" type="&#x22;Iterable[str] | None&#x22;" value="&#x22;None&#x22;">
          Optional iterable of event type strings to filter.
          If None, captures all event types.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_testing.hooks.CapturedEvents&#x22;">
        A CapturedEvents instance containing the collected events.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;sample_ingestion_event&#x22;" type="&#x22;() -> IngestionEvent&#x22;">
      Return a sample ingestion event for tests.

      Creates a pre-configured IngestionEvent representing a successful
      data ingestion operation for testing hook handlers and event processing.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > event = sample\_ingestion\_event()
        > > > assert event.event\_type == "ingestion.end"
        > > > assert event.status == "success"
      </Callout>

      <PySourceCode>
        ```python
        def sample_ingestion_event() -> IngestionEvent:
            """Return a sample ingestion event for tests.

            Creates a pre-configured IngestionEvent representing a successful
            data ingestion operation for testing hook handlers and event processing.

            Returns:
                An IngestionEvent with sample data.

            Example:
                >>> event = sample_ingestion_event()
                >>> assert event.event_type == "ingestion.end"
                >>> assert event.status == "success"

            """
            return IngestionEvent(
                event_type="ingestion.end",
                asset_key="dlt_sample",
                table_name="bronze.sample",
                group_name="sample",
                partition_key="2024-01-01",
                status="success",
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.hooks.IngestionEvent&#x22;">
        An IngestionEvent with sample data.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;sample_quality_event&#x22;" type="&#x22;() -> QualityResultEvent&#x22;">
      Return a sample quality check event for tests.

      Creates a pre-configured QualityResultEvent representing a passed
      data quality check for testing hook handlers.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > event = sample\_quality\_event()
        > > > assert event.event\_type == "quality.result"
        > > > assert event.passed is True
      </Callout>

      <PySourceCode>
        ```python
        def sample_quality_event() -> QualityResultEvent:
            """Return a sample quality check event for tests.

            Creates a pre-configured QualityResultEvent representing a passed
            data quality check for testing hook handlers.

            Returns:
                A QualityResultEvent with sample data.

            Example:
                >>> event = sample_quality_event()
                >>> assert event.event_type == "quality.result"
                >>> assert event.passed is True

            """
            return QualityResultEvent(
                event_type="quality.result",
                asset_key="sample_asset",
                check_name="null_check",
                passed=True,
                check_type="NullCheck",
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.hooks.QualityResultEvent&#x22;">
        A QualityResultEvent with sample data.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;sample_transform_event&#x22;" type="&#x22;() -> TransformEvent&#x22;">
      Return a sample transform event for tests.

      Creates a pre-configured TransformEvent representing a successful
      dbt transformation for testing hook handlers.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > event = sample\_transform\_event()
        > > > assert event.event\_type == "transform.end"
        > > > assert event.tool == "dbt"
      </Callout>

      <PySourceCode>
        ```python
        def sample_transform_event() -> TransformEvent:
            """Return a sample transform event for tests.

            Creates a pre-configured TransformEvent representing a successful
            dbt transformation for testing hook handlers.

            Returns:
                A TransformEvent with sample data.

            Example:
                >>> event = sample_transform_event()
                >>> assert event.event_type == "transform.end"
                >>> assert event.tool == "dbt"

            """
            return TransformEvent(
                event_type="transform.end",
                tool="dbt",
                status="success",
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.hooks.TransformEvent&#x22;">
        A TransformEvent with sample data.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;sample_publish_event&#x22;" type="&#x22;() -> PublishEvent&#x22;">
      Return a sample publish event for tests.

      Creates a pre-configured PublishEvent representing a successful
      data publication to Postgres for testing hook handlers.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > event = sample\_publish\_event()
        > > > assert event.event\_type == "publish.end"
        > > > assert event.target\_system == "postgres"
      </Callout>

      <PySourceCode>
        ```python
        def sample_publish_event() -> PublishEvent:
            """Return a sample publish event for tests.

            Creates a pre-configured PublishEvent representing a successful
            data publication to Postgres for testing hook handlers.

            Returns:
                A PublishEvent with sample data.

            Example:
                >>> event = sample_publish_event()
                >>> assert event.event_type == "publish.end"
                >>> assert event.target_system == "postgres"

            """
            return PublishEvent(
                event_type="publish.end",
                asset_key="publish_sample_marts",
                target_system="postgres",
                tables={"sample": "marts.sample"},
                status="success",
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.hooks.PublishEvent&#x22;">
        A PublishEvent with sample data.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;sample_lineage_event&#x22;" type="&#x22;() -> LineageEvent&#x22;">
      Return a sample lineage event for tests.

      Creates a pre-configured LineageEvent representing data lineage
      between raw and marts tables for testing hook handlers.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > event = sample\_lineage\_event()
        > > > assert event.event\_type == "lineage.edges"
        > > > assert ("raw\.sample", "marts.sample") in event.edges
      </Callout>

      <PySourceCode>
        ```python
        def sample_lineage_event() -> LineageEvent:
            """Return a sample lineage event for tests.

            Creates a pre-configured LineageEvent representing data lineage
            between raw and marts tables for testing hook handlers.

            Returns:
                A LineageEvent with sample data.

            Example:
                >>> event = sample_lineage_event()
                >>> assert event.event_type == "lineage.edges"
                >>> assert ("raw.sample", "marts.sample") in event.edges

            """
            return LineageEvent(
                event_type="lineage.edges",
                edges=[("raw.sample", "marts.sample")],
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.hooks.LineageEvent&#x22;">
        A LineageEvent with sample data.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;sample_telemetry_event&#x22;" type="&#x22;() -> TelemetryEvent&#x22;">
      Return a sample telemetry event for tests.

      Creates a pre-configured TelemetryEvent representing a metric
      emission for testing hook handlers.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > event = sample\_telemetry\_event()
        > > > assert event.event\_type == "telemetry.metric"
        > > > assert event.name == "sample\_metric"
      </Callout>

      <PySourceCode>
        ```python
        def sample_telemetry_event() -> TelemetryEvent:
            """Return a sample telemetry event for tests.

            Creates a pre-configured TelemetryEvent representing a metric
            emission for testing hook handlers.

            Returns:
                A TelemetryEvent with sample data.

            Example:
                >>> event = sample_telemetry_event()
                >>> assert event.event_type == "telemetry.metric"
                >>> assert event.name == "sample_metric"

            """
            return TelemetryEvent(
                event_type="telemetry.metric",
                name="sample_metric",
                value=1,
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.hooks.TelemetryEvent&#x22;">
        A TelemetryEvent with sample data.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;sample_service_event&#x22;" type="&#x22;() -> ServiceLifecycleEvent&#x22;">
      Return a sample service lifecycle event for tests.

      Creates a pre-configured ServiceLifecycleEvent representing a service
      startup event for testing hook handlers.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > event = sample\_service\_event()
        > > > assert event.event\_type == "service.post\_start"
        > > > assert event.service\_name == "postgres"
      </Callout>

      <PySourceCode>
        ```python
        def sample_service_event() -> ServiceLifecycleEvent:
            """Return a sample service lifecycle event for tests.

            Creates a pre-configured ServiceLifecycleEvent representing a service
            startup event for testing hook handlers.

            Returns:
                A ServiceLifecycleEvent with sample data.

            Example:
                >>> event = sample_service_event()
                >>> assert event.event_type == "service.post_start"
                >>> assert event.service_name == "postgres"

            """
            return ServiceLifecycleEvent(
                event_type="service.post_start",
                service_name="postgres",
                phase="post_start",
                status="success",
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.hooks.ServiceLifecycleEvent&#x22;">
        A ServiceLifecycleEvent with sample data.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
