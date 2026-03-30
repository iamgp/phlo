# OtelHookPlugin (/docs/python-reference/packages/phlo-otel/phlo_otel/hooks_plugin/OtelHookPlugin)



Emit OTel traces and metrics from Phlo hook events.

This plugin translates Phlo hook events into OpenTelemetry spans and metrics,
providing comprehensive observability for data pipelines. It handles event
correlation, trace context propagation, and standardized metric collection.

The plugin supports the following event types:

* Ingestion: Tracks data ingestion operations with row counts and duration
* Transform: Monitors transformation tools (dbt, etc.) with metrics
* Quality: Records quality check results with pass/fail status
* Lineage: Captures data lineage edge information
* Publish: Tracks data publishing to external systems
* Service Lifecycle: Monitors service startup/shutdown phases
* Schema Migration: Records DDL changes and schema evolution
* Data Migration: Tracks data movement operations
* Telemetry: Handles custom telemetry metrics
* Logs: Exports structured logs to OTel

Attributes [#attributes]

<PyAttribute name="&#x22;_counter_cache&#x22;" type="&#x22;dict[tuple[str, str], Any]&#x22;" value="&#x22;{}&#x22;">
  Cache for counter instruments to avoid recreation.
</PyAttribute>

<PyAttribute name="&#x22;_gauge_cache&#x22;" type="&#x22;dict[tuple[str, str], Any]&#x22;" value="&#x22;{}&#x22;">
  Cache for gauge instruments to avoid recreation.
</PyAttribute>

<PyAttribute name="&#x22;_histogram_cache&#x22;" type="&#x22;dict[tuple[str, str], Any]&#x22;" value="&#x22;{}&#x22;">
  Cache for histogram instruments to avoid recreation.
</PyAttribute>

<PyAttribute name="&#x22;_up_down_counter_cache&#x22;" type="&#x22;dict[tuple[str, str], Any]&#x22;" value="&#x22;{}&#x22;">
  Cache for up-down counter instruments.
</PyAttribute>

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for discovery and identification.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self) -> None&#x22;">
  Initialize the OtelHookPlugin with empty instrument caches.

  <PySourceCode>
    ```python
    def __init__(self) -> None:
        """Initialize the OtelHookPlugin with empty instrument caches."""
        self._counter_cache: dict[tuple[str, str], Any] = {}
        self._gauge_cache: dict[tuple[str, str], Any] = {}
        self._histogram_cache: dict[tuple[str, str], Any] = {}
        self._up_down_counter_cache: dict[tuple[str, str], Any] = {}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_hooks&#x22;" type="&#x22;(self) -> list[HookRegistration]&#x22;">
  Return list of hook registrations for event handling.

  Registers handlers for all supported Phlo event types, mapping each
  event to the appropriate OTel instrumentation logic.

  <PySourceCode>
    ```python
    def get_hooks(self) -> list[HookRegistration]:
        """Return list of hook registrations for event handling.

                Registers handlers for all supported Phlo event types, mapping each
        event to the appropriate OTel instrumentation logic.

        Returns:
                    list[HookRegistration]: List of 10 hook registrations covering
                        all major Phlo event types.

        """
        return [
            HookRegistration(
                hook_name="otel_ingestion",
                handler=self._handle_ingestion,
            ),
            HookRegistration(
                hook_name="otel_transform",
                handler=self._handle_transform,
            ),
            HookRegistration(
                hook_name="otel_quality",
                handler=self._handle_quality,
            ),
            HookRegistration(
                hook_name="otel_lineage",
                handler=self._handle_lineage,
            ),
            HookRegistration(
                hook_name="otel_publish",
                handler=self._handle_publish,
            ),
            HookRegistration(
                hook_name="otel_service_lifecycle",
                handler=self._handle_service_lifecycle,
            ),
            HookRegistration(
                hook_name="otel_schema_migration",
                handler=self._handle_schema_migration,
            ),
            HookRegistration(
                hook_name="otel_data_migration",
                handler=self._handle_data_migration,
            ),
            HookRegistration(
                hook_name="otel_telemetry",
                handler=self._handle_telemetry,
            ),
            HookRegistration(
                hook_name="otel_log_record",
                handler=self._handle_log_record,
            ),
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[HookRegistration]: List of 10 hook registrations covering
    all major Phlo event types.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_handle_ingestion&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Handle IngestionEvent and emit OTel spans and metrics.

  Creates a span representing the ingestion operation with attributes
  for table name, group, status, and metrics. Also records counters for
  ingestion runs and rows processed, plus a duration histogram.

  <Callout title="&#x22;Side Effects&#x22;" type="&#x22;side-effects&#x22;">
    * Creates OTel span with ingestion attributes
    * Records phlo.ingestion.runs counter
    * Records phlo.ingestion.rows counter (if rows\_loaded available)
    * Records phlo.ingestion.duration histogram (if duration available)
    * Records phlo.errors counter on failure
  </Callout>

  <PySourceCode>
    ```python
    def _handle_ingestion(self, event: Any) -> None:
        """Handle IngestionEvent and emit OTel spans and metrics.

        Creates a span representing the ingestion operation with attributes
        for table name, group, status, and metrics. Also records counters for
        ingestion runs and rows processed, plus a duration histogram.

        Args:
            event: The IngestionEvent to process. Expected to be an instance
                of IngestionEvent with table_name, group_name, status, and
                metrics attributes.

        Side Effects:
            - Creates OTel span with ingestion attributes
            - Records phlo.ingestion.runs counter
            - Records phlo.ingestion.rows counter (if rows_loaded available)
            - Records phlo.ingestion.duration histogram (if duration available)
            - Records phlo.errors counter on failure

        """
        if not isinstance(event, IngestionEvent):
            return

        correlation = self._merge_correlation(
            event.correlation,
            run_id=event.run_id,
            asset_key=event.asset_key,
            partition_key=event.partition_key,
        )
        tracer = get_tracer()
        with tracer.start_as_current_span(
            f"ingestion.{event.table_name}",
            attributes={
                "phlo.asset_key": event.asset_key,
                "phlo.stage": "ingestion",
                "phlo.table_name": event.table_name,
                "phlo.group_name": event.group_name,
                "phlo.event_type": event.event_type,
            },
            context=self._build_parent_context(correlation),
        ) as span:
            self._set_correlation_attributes(span, correlation)
            self._set_attribute_if_present(span, "phlo.system", event.tags.get("source"))
            if event.status:
                span.set_attribute("phlo.status", event.status)
            if event.error:
                span.set_status(Status(status_code=StatusCode.ERROR, description=event.error))
            if event.metrics:
                for key, value in event.metrics.items():
                    if isinstance(value, (int, float)):
                        span.set_attribute(f"phlo.metrics.{key}", value)
            self._set_event_tags(span, event.tags)
            self._record_failure(event_name="ingestion", status=event.status, error=event.error)

        counter = self._get_counter(
            "phlo.ingestion.runs",
            description="Number of ingestion runs",
        )
        counter.add(1, {"table_name": event.table_name, "status": event.status or "unknown"})

        rows = event.metrics.get("rows_loaded")
        if rows is None:
            rows = event.metrics.get("rows_processed")
        if isinstance(rows, (int, float)):
            rows_counter = self._get_counter(
                "phlo.ingestion.rows",
                description="Rows ingested",
            )
            rows_counter.add(int(rows), {"table_name": event.table_name})

        self._record_duration(
            "phlo.ingestion.duration",
            metrics=event.metrics,
            attributes={"table_name": event.table_name, "status": event.status or "unknown"},
            description="Ingestion duration",
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The IngestionEvent to process. Expected to be an instance
      of IngestionEvent with table\_name, group\_name, status, and
      metrics attributes.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_handle_transform&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Handle TransformEvent and emit OTel spans and metrics.

  Creates a span for transformation operations (dbt, etc.) with
  attributes for tool, target, and model names. Records transform
  runs counter and duration histogram.

  <Callout title="&#x22;Side Effects&#x22;" type="&#x22;side-effects&#x22;">
    * Creates OTel span with transform attributes
    * Records phlo.transform.runs counter
    * Records phlo.transform.duration histogram (if duration available)
    * Records phlo.errors counter on failure
  </Callout>

  <PySourceCode>
    ```python
    def _handle_transform(self, event: Any) -> None:
        """Handle TransformEvent and emit OTel spans and metrics.

        Creates a span for transformation operations (dbt, etc.) with
        attributes for tool, target, and model names. Records transform
        runs counter and duration histogram.

        Args:
            event: The TransformEvent to process. Expected to have tool,
                target, model_names, status, and metrics attributes.

        Side Effects:
            - Creates OTel span with transform attributes
            - Records phlo.transform.runs counter
            - Records phlo.transform.duration histogram (if duration available)
            - Records phlo.errors counter on failure

        """
        if not isinstance(event, TransformEvent):
            return

        correlation = self._merge_correlation(
            event.correlation,
            run_id=getattr(event, "run_id", None),
            asset_key=event.asset_key,
            partition_key=event.partition_key,
        )
        tracer = get_tracer()
        span_name = f"transform.{event.tool}"
        if event.target:
            span_name = f"transform.{event.tool}.{event.target}"

        with tracer.start_as_current_span(
            span_name,
            attributes={
                "phlo.stage": "transform",
                "phlo.system": event.tool,
                "phlo.tool": event.tool,
                "phlo.event_type": event.event_type,
            },
            context=self._build_parent_context(correlation),
        ) as span:
            self._set_correlation_attributes(span, correlation)
            if event.target:
                span.set_attribute("phlo.target", event.target)
            if event.model_names:
                span.set_attribute("phlo.model_names", event.model_names)
            if event.status:
                span.set_attribute("phlo.status", event.status)
            if event.error:
                span.set_status(Status(status_code=StatusCode.ERROR, description=event.error))
            self._set_numeric_span_attributes(span, event.metrics)
            self._set_event_tags(span, event.tags)
            self._record_failure(event_name="transform", status=event.status, error=event.error)

        counter = self._get_counter(
            "phlo.transform.runs",
            description="Number of transform runs",
        )
        counter.add(1, {"tool": event.tool, "status": event.status or "unknown"})

        self._record_duration(
            "phlo.transform.duration",
            metrics=event.metrics,
            attributes={"tool": event.tool, "status": event.status or "unknown"},
            description="Transform duration",
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The TransformEvent to process. Expected to have tool,
      target, model\_names, status, and metrics attributes.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_handle_quality&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Handle QualityResultEvent and emit OTel spans and metrics.

  Creates a span for quality check results with pass/fail status,
  severity, and check metadata. Sets error status on the span for
  failed checks and records quality check counter.

  <Callout title="&#x22;Side Effects&#x22;" type="&#x22;side-effects&#x22;">
    * Creates OTel span with quality check attributes
    * Sets span status to ERROR for failed checks
    * Records phlo.quality.checks counter with pass/fail result
    * Records phlo.errors counter on failure
  </Callout>

  <PySourceCode>
    ```python
    def _handle_quality(self, event: Any) -> None:
        """Handle QualityResultEvent and emit OTel spans and metrics.

        Creates a span for quality check results with pass/fail status,
        severity, and check metadata. Sets error status on the span for
        failed checks and records quality check counter.

        Args:
            event: The QualityResultEvent to process. Expected to have
                check_name, passed, severity, check_type, and metadata.

        Side Effects:
            - Creates OTel span with quality check attributes
            - Sets span status to ERROR for failed checks
            - Records phlo.quality.checks counter with pass/fail result
            - Records phlo.errors counter on failure

        """
        if not isinstance(event, QualityResultEvent):
            return

        correlation = self._merge_correlation(
            event.correlation,
            run_id=getattr(event, "run_id", None),
            asset_key=event.asset_key,
            partition_key=event.partition_key,
            check_name=event.check_name,
        )
        tracer = get_tracer()
        with tracer.start_as_current_span(
            f"quality.{event.check_name}",
            attributes={
                "phlo.asset_key": event.asset_key,
                "phlo.stage": "quality",
                "phlo.check_name": event.check_name,
                "phlo.passed": event.passed,
                "phlo.event_type": event.event_type,
            },
            context=self._build_parent_context(correlation),
        ) as span:
            self._set_correlation_attributes(span, correlation)
            self._set_attribute_if_present(span, "phlo.system", event.tags.get("backend"))
            self._set_attribute_if_present(span, "phlo.operation", event.check_type)
            if event.severity:
                span.set_attribute("phlo.severity", event.severity)
            if event.check_type:
                span.set_attribute("phlo.check_type", event.check_type)
            for key, value in event.metadata.items():
                if isinstance(value, (bool, int, float, str)):
                    span.set_attribute(f"phlo.metadata.{key}", value)
            if not event.passed:
                span.set_status(
                    Status(
                        status_code=StatusCode.ERROR,
                        description=f"Quality check failed: {event.check_name}",
                    )
                )
                self._record_failure(event_name="quality", status="fail")
            self._set_event_tags(span, event.tags)

        counter = self._get_counter(
            "phlo.quality.checks",
            description="Quality check executions",
        )
        result = "pass" if event.passed else "fail"
        counter.add(1, {"check_name": event.check_name, "result": result})
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The QualityResultEvent to process. Expected to have
      check\_name, passed, severity, check\_type, and metadata.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_handle_lineage&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Handle LineageEvent and emit OTel spans and metrics.

  Creates a span for lineage tracking with edge count and asset keys.
  Records counters for lineage events and edges with attributes from tags.

  <Callout title="&#x22;Side Effects&#x22;" type="&#x22;side-effects&#x22;">
    * Creates OTel span with lineage attributes
    * Records phlo.lineage.events counter
    * Records phlo.lineage.edges counter
  </Callout>

  <PySourceCode>
    ```python
    def _handle_lineage(self, event: Any) -> None:
        """Handle LineageEvent and emit OTel spans and metrics.

        Creates a span for lineage tracking with edge count and asset keys.
        Records counters for lineage events and edges with attributes from tags.

        Args:
            event: The LineageEvent to process. Expected to have edges,
                asset_keys, metadata, and tags.

        Side Effects:
            - Creates OTel span with lineage attributes
            - Records phlo.lineage.events counter
            - Records phlo.lineage.edges counter

        """
        if not isinstance(event, LineageEvent):
            return

        correlation = self._merge_correlation(event.correlation)
        tracer = get_tracer()
        with tracer.start_as_current_span(
            "lineage.edges",
            attributes={
                "phlo.event_type": event.event_type,
                "phlo.stage": "lineage",
                "phlo.operation": "edges",
                "phlo.edge_count": len(event.edges),
                "phlo.asset_count": len(event.asset_keys),
            },
            context=self._build_parent_context(correlation),
        ) as span:
            self._set_correlation_attributes(span, correlation)
            if event.asset_keys:
                span.set_attribute("phlo.asset_keys", sorted(event.asset_keys))
            self._set_event_tags(span, event.tags)
            for key, value in event.metadata.items():
                if isinstance(value, (bool, int, float, str)):
                    span.set_attribute(f"phlo.metadata.{key}", value)

        event_counter = self._get_counter(
            "phlo.lineage.events",
            description="Number of lineage events",
        )
        edge_counter = self._get_counter(
            "phlo.lineage.edges",
            description="Number of lineage edges",
        )
        attributes = self._metric_attributes_from_tags(event.tags)
        event_counter.add(1, attributes)
        edge_counter.add(len(event.edges), attributes)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The LineageEvent to process. Expected to have edges,
      asset\_keys, metadata, and tags.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_handle_publish&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Handle PublishEvent and emit OTel spans and metrics.

  Creates a span for data publishing operations with attributes for
  target system, tables, and metrics. Records publish runs counter and
  table count, plus duration histogram.

  Side Effects:

  * Creates OTel span with publish attributes
  * Records phlo.publish.runs counter
  * Records phlo.publish.tables counter (if tables present)
  * Records phlo.publish.duration histogram (if duration available)
  * Records phlo.errors counter on failure

  <PySourceCode>
    ```python
    def _handle_publish(self, event: Any) -> None:
        """Handle PublishEvent and emit OTel spans and metrics.

                Creates a span for data publishing operations with attributes for
        target system, tables, and metrics. Records publish runs counter and
        table count, plus duration histogram.

        Args:
                    event: The PublishEvent to process. Expected to have target_system,
                        tables, status, metrics, and optional error.

                Side Effects:
                    - Creates OTel span with publish attributes
                    - Records phlo.publish.runs counter
                    - Records phlo.publish.tables counter (if tables present)
                    - Records phlo.publish.duration histogram (if duration available)
                    - Records phlo.errors counter on failure

        """
        if not isinstance(event, PublishEvent):
            return

        correlation = self._merge_correlation(
            event.correlation,
            run_id=getattr(event, "run_id", None),
            asset_key=event.asset_key,
            partition_key=getattr(event, "partition_key", None),
        )
        target_system = event.target_system or "unknown"
        tracer = get_tracer()
        with tracer.start_as_current_span(
            f"publish.{target_system}",
            attributes={
                "phlo.event_type": event.event_type,
                "phlo.stage": "publish",
                "phlo.system": target_system,
                "phlo.operation": "publish",
                "phlo.target_system": target_system,
            },
            context=self._build_parent_context(correlation),
        ) as span:
            self._set_correlation_attributes(span, correlation)
            if event.status:
                span.set_attribute("phlo.status", event.status)
            if event.tables:
                span.set_attribute("phlo.table_count", len(event.tables))
                span.set_attribute("phlo.tables", sorted(event.tables.values()))
            if event.error:
                span.set_status(Status(status_code=StatusCode.ERROR, description=event.error))
            self._set_numeric_span_attributes(span, event.metrics)
            self._set_event_tags(span, event.tags)
            self._record_failure(event_name="publish", status=event.status, error=event.error)

        counter = self._get_counter(
            "phlo.publish.runs",
            description="Number of publish runs",
        )
        counter.add(1, {"target_system": target_system, "status": event.status or "unknown"})

        if event.tables:
            table_counter = self._get_counter(
                "phlo.publish.tables",
                description="Number of published tables",
            )
            table_counter.add(len(event.tables), {"target_system": target_system})

        self._record_duration(
            "phlo.publish.duration",
            metrics=event.metrics,
            attributes={"target_system": target_system, "status": event.status or "unknown"},
            description="Publish duration",
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The PublishEvent to process. Expected to have target\_system,
      tables, status, metrics, and optional error.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_handle_service_lifecycle&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Handle ServiceLifecycleEvent and emit OTel spans and metrics.

  Creates a span for service lifecycle phases (start, stop, health check)
  with service name and phase attributes. Sets error status for failed
  phases and records lifecycle event counter.

  <Callout title="&#x22;Side Effects&#x22;" type="&#x22;side-effects&#x22;">
    * Creates OTel span with service lifecycle attributes
    * Sets span status to ERROR for failed phases
    * Records phlo.service.lifecycle.events counter
    * Records phlo.errors counter on failure
  </Callout>

  <PySourceCode>
    ```python
    def _handle_service_lifecycle(self, event: Any) -> None:
        """Handle ServiceLifecycleEvent and emit OTel spans and metrics.

        Creates a span for service lifecycle phases (start, stop, health check)
        with service name and phase attributes. Sets error status for failed
        phases and records lifecycle event counter.

        Args:
            event: The ServiceLifecycleEvent to process. Expected to have
                service_name, phase, status, and optional project/container info.

        Side Effects:
            - Creates OTel span with service lifecycle attributes
            - Sets span status to ERROR for failed phases
            - Records phlo.service.lifecycle.events counter
            - Records phlo.errors counter on failure

        """
        if not isinstance(event, ServiceLifecycleEvent):
            return

        correlation = self._merge_correlation(event.correlation)
        phase = event.phase or "unknown"
        tracer = get_tracer()
        with tracer.start_as_current_span(
            f"service.{event.service_name}.{phase}",
            attributes={
                "phlo.event_type": event.event_type,
                "phlo.stage": "service",
                "phlo.system": "service",
                "phlo.operation": phase,
                "phlo.service_name": event.service_name,
                "phlo.phase": phase,
            },
            context=self._build_parent_context(correlation),
        ) as span:
            self._set_correlation_attributes(span, correlation)
            if event.project_name:
                span.set_attribute("phlo.project_name", event.project_name)
            if event.project_root:
                span.set_attribute("phlo.project_root", event.project_root)
            if event.container_name:
                span.set_attribute("phlo.container_name", event.container_name)
            if event.status:
                span.set_attribute("phlo.status", event.status)
                if self._is_failure_status(event.status):
                    span.set_status(
                        Status(
                            status_code=StatusCode.ERROR,
                            description=f"Service lifecycle failed: {phase}",
                        )
                    )
            self._set_event_tags(span, event.tags)
            self._record_failure(event_name="service_lifecycle", status=event.status)

        counter = self._get_counter(
            "phlo.service.lifecycle.events",
            description="Number of service lifecycle events",
        )
        counter.add(
            1,
            {
                "service_name": event.service_name,
                "phase": phase,
                "status": event.status or "unknown",
            },
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The ServiceLifecycleEvent to process. Expected to have
      service\_name, phase, status, and optional project/container info.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_handle_schema_migration&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Handle SchemaMigrationEvent and emit OTel spans and metrics.

  Creates a span for DDL/schema changes with table name, classification,
  and change count. Records migration runs counter and changes counter,
  setting error status for failed migrations.

  <Callout title="&#x22;Side Effects&#x22;" type="&#x22;side-effects&#x22;">
    * Creates OTel span with schema migration attributes
    * Sets span status to ERROR for failed migrations
    * Records phlo.schema\_migration.runs counter
    * Records phlo.schema\_migration.changes counter
    * Records phlo.errors counter on failure
  </Callout>

  <PySourceCode>
    ```python
    def _handle_schema_migration(self, event: Any) -> None:
        """Handle SchemaMigrationEvent and emit OTel spans and metrics.

        Creates a span for DDL/schema changes with table name, classification,
        and change count. Records migration runs counter and changes counter,
        setting error status for failed migrations.

        Args:
            event: The SchemaMigrationEvent to process. Expected to have
                table_name, classification, change_count, status, and changes.

        Side Effects:
            - Creates OTel span with schema migration attributes
            - Sets span status to ERROR for failed migrations
            - Records phlo.schema_migration.runs counter
            - Records phlo.schema_migration.changes counter
            - Records phlo.errors counter on failure

        """
        if not isinstance(event, SchemaMigrationEvent):
            return

        correlation = self._merge_correlation(event.correlation)
        tracer = get_tracer()
        with tracer.start_as_current_span(
            f"schema_migration.{event.table_name}",
            attributes={
                "phlo.event_type": event.event_type,
                "phlo.stage": "migration",
                "phlo.system": "schema",
                "phlo.operation": "schema_migration",
                "phlo.table_name": event.table_name,
                "phlo.classification": event.classification,
                "phlo.change_count": event.change_count,
                "phlo.status": event.status,
            },
            context=self._build_parent_context(correlation),
        ) as span:
            self._set_correlation_attributes(span, correlation)
            if event.changes:
                span.set_attribute("phlo.schema_change_count", len(event.changes))
            self._set_event_tags(span, event.tags)
            if self._is_failure_status(event.status):
                span.set_status(
                    Status(
                        status_code=StatusCode.ERROR,
                        description=f"Schema migration failed: {event.table_name}",
                    )
                )
            self._record_failure(event_name="schema_migration", status=event.status)

        labels = {"classification": event.classification, "status": event.status}
        counter = self._get_counter(
            "phlo.schema_migration.runs",
            description="Number of schema migration events",
        )
        counter.add(1, labels)

        changes_counter = self._get_counter(
            "phlo.schema_migration.changes",
            description="Schema change count",
        )
        changes_counter.add(event.change_count, labels)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The SchemaMigrationEvent to process. Expected to have
      table\_name, classification, change\_count, status, and changes.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_handle_data_migration&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Handle DataMigrationEvent and emit OTel spans and metrics.

  Creates a span for data migration operations with source type,
  destination table, and row counts. Records migration runs counter,
  rows read/written counters, and duration histogram.

  <Callout title="&#x22;Side Effects&#x22;" type="&#x22;side-effects&#x22;">
    * Creates OTel span with data migration attributes
    * Sets span status to ERROR for failed migrations
    * Records phlo.data\_migration.runs counter
    * Records phlo.data\_migration.rows\_read counter
    * Records phlo.data\_migration.rows\_written counter
    * Records phlo.data\_migration.duration histogram
    * Records phlo.errors counter on failure
  </Callout>

  <PySourceCode>
    ```python
    def _handle_data_migration(self, event: Any) -> None:
        """Handle DataMigrationEvent and emit OTel spans and metrics.

        Creates a span for data migration operations with source type,
        destination table, and row counts. Records migration runs counter,
        rows read/written counters, and duration histogram.

        Args:
            event: The DataMigrationEvent to process. Expected to have
                migration_name, source_type, destination_table, rows_read,
                rows_written, status, and metrics.

        Side Effects:
            - Creates OTel span with data migration attributes
            - Sets span status to ERROR for failed migrations
            - Records phlo.data_migration.runs counter
            - Records phlo.data_migration.rows_read counter
            - Records phlo.data_migration.rows_written counter
            - Records phlo.data_migration.duration histogram
            - Records phlo.errors counter on failure

        """
        if not isinstance(event, DataMigrationEvent):
            return

        correlation = self._merge_correlation(
            event.correlation,
            run_id=getattr(event, "run_id", None),
        )
        tracer = get_tracer()
        with tracer.start_as_current_span(
            f"data_migration.{event.migration_name}",
            attributes={
                "phlo.event_type": event.event_type,
                "phlo.stage": "migration",
                "phlo.system": event.source_type,
                "phlo.operation": "data_migration",
                "phlo.migration_name": event.migration_name,
                "phlo.source_type": event.source_type,
                "phlo.destination_table": event.destination_table,
                "phlo.rows_read": event.rows_read,
                "phlo.rows_written": event.rows_written,
                "phlo.status": event.status,
            },
            context=self._build_parent_context(correlation),
        ) as span:
            self._set_correlation_attributes(span, correlation)
            if event.chunk_index is not None:
                span.set_attribute("phlo.chunk_index", event.chunk_index)
            self._set_numeric_span_attributes(span, event.metrics)
            self._set_event_tags(span, event.tags)
            if self._is_failure_status(event.status):
                span.set_status(
                    Status(
                        status_code=StatusCode.ERROR,
                        description=f"Data migration failed: {event.migration_name}",
                    )
                )
            self._record_failure(event_name="data_migration", status=event.status)

        labels = {"source_type": event.source_type, "status": event.status}
        runs_counter = self._get_counter(
            "phlo.data_migration.runs",
            description="Number of data migration events",
        )
        runs_counter.add(1, labels)

        rows_read_counter = self._get_counter(
            "phlo.data_migration.rows_read",
            description="Rows read during data migration",
        )
        rows_read_counter.add(event.rows_read, labels)

        rows_written_counter = self._get_counter(
            "phlo.data_migration.rows_written",
            description="Rows written during data migration",
        )
        rows_written_counter.add(event.rows_written, labels)

        self._record_duration(
            "phlo.data_migration.duration",
            metrics=event.metrics,
            attributes=labels,
            description="Data migration duration",
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The DataMigrationEvent to process. Expected to have
      migration\_name, source\_type, destination\_table, rows\_read,
      rows\_written, status, and metrics.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_handle_telemetry&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Handle TelemetryEvent and emit OTel metrics.

  Routes telemetry events to the appropriate metric instrument based on
  the metric\_kind in the payload. Supports counter, gauge, histogram, and
  up\_down\_counter metric types.

  Side Effects:

  * Creates or retrieves cached metric instrument
  * Records value to the appropriate instrument

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    Non-numeric values are silently ignored.
    Special handling for iceberg.maintenance.\* metrics which are
    promoted to standard phlo.maintenance.\* metrics.
  </Callout>

  <PySourceCode>
    ```python
    def _handle_telemetry(self, event: Any) -> None:
        """Handle TelemetryEvent and emit OTel metrics.

                Routes telemetry events to the appropriate metric instrument based on
        the metric_kind in the payload. Supports counter, gauge, histogram, and
        up_down_counter metric types.

        Args:
                    event: The TelemetryEvent to process. Expected to have name,
                        value (numeric), unit, and payload with metric_kind.

                Side Effects:
                    - Creates or retrieves cached metric instrument
                    - Records value to the appropriate instrument

        Note:
                    Non-numeric values are silently ignored.
                    Special handling for iceberg.maintenance.* metrics which are
                    promoted to standard phlo.maintenance.* metrics.

        """
        if not isinstance(event, TelemetryEvent):
            return
        if event.event_type != "telemetry.metric":
            return
        if not isinstance(event.value, (int, float)):
            return
        if self._handle_maintenance_telemetry(event):
            return

        metric_name = f"phlo.telemetry.{event.name}"
        metric_kind = self._resolve_metric_kind(event.payload)
        attributes = self._normalize_metric_attributes(event.payload)
        unit = event.unit or ""

        if metric_kind == "counter":
            counter = self._get_counter(
                metric_name,
                description=f"Telemetry metric: {event.name}",
                unit=unit,
            )
            counter.add(event.value, attributes)
            return

        if metric_kind == "histogram":
            histogram = self._get_histogram(
                metric_name,
                unit=unit,
                description=f"Telemetry metric: {event.name}",
            )
            histogram.record(event.value, attributes)
            return

        if metric_kind == "up_down_counter":
            counter = self._get_up_down_counter(
                metric_name,
                unit=unit,
                description=f"Telemetry metric: {event.name}",
            )
            counter.add(event.value, attributes)
            return

        gauge = self._get_gauge(
            metric_name,
            unit=unit,
            description=f"Telemetry metric: {event.name}",
        )
        gauge.set(event.value, attributes)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The TelemetryEvent to process. Expected to have name,
      value (numeric), unit, and payload with metric\_kind.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_handle_maintenance_telemetry&#x22;" type="&#x22;(self, event) -> bool&#x22;">
  Handle Iceberg maintenance telemetry events.

  Maps iceberg.maintenance.\* telemetry events to standard Phlo maintenance
  metrics with consistent naming and attributes.

  <Callout title="&#x22;Side Effects&#x22;" type="&#x22;side-effects&#x22;">
    * Records maintenance metrics to counter or histogram instruments
  </Callout>

  <PySourceCode>
    ```python
    def _handle_maintenance_telemetry(self, event: TelemetryEvent) -> bool:
        """Handle Iceberg maintenance telemetry events.

        Maps iceberg.maintenance.* telemetry events to standard Phlo maintenance
        metrics with consistent naming and attributes.

        Args:
            event: The TelemetryEvent to check and process.

        Returns:
            bool: True if the event was handled (is a maintenance event),
                False otherwise.

        Side Effects:
            - Records maintenance metrics to counter or histogram instruments

        """
        if not event.name.startswith("iceberg.maintenance."):
            return False

        attributes = {
            **self._metric_attributes_from_tags(event.tags),
            **self._normalize_metric_attributes(event.payload),
        }
        metric_map: dict[str, tuple[str, str]] = {
            "iceberg.maintenance.run": ("counter", "phlo.maintenance.runs"),
            "iceberg.maintenance.duration_seconds": ("histogram", "phlo.maintenance.duration"),
            "iceberg.maintenance.tables_processed": (
                "counter",
                "phlo.maintenance.tables_processed",
            ),
            "iceberg.maintenance.errors": ("counter", "phlo.maintenance.errors"),
            "iceberg.maintenance.snapshots_deleted": (
                "counter",
                "phlo.maintenance.snapshots_deleted",
            ),
            "iceberg.maintenance.orphan_files": ("counter", "phlo.maintenance.orphan_files"),
            "iceberg.maintenance.total_records": ("counter", "phlo.maintenance.records_processed"),
            "iceberg.maintenance.total_size_mb": ("histogram", "phlo.maintenance.size_mb"),
        }
        mapping = metric_map.get(event.name)
        if mapping is None:
            return False

        metric_type, metric_name = mapping
        if metric_type == "counter":
            counter = self._get_counter(
                metric_name,
                description=f"Maintenance metric derived from {event.name}",
                unit=event.unit or "",
            )
            counter.add(event.value, attributes)
            return True

        histogram = self._get_histogram(
            metric_name,
            description=f"Maintenance metric derived from {event.name}",
            unit=event.unit or "",
        )
        histogram.record(event.value, attributes)
        return True
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;TelemetryEvent&#x22;" value="undefined">
      The TelemetryEvent to check and process.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if the event was handled (is a maintenance event),
    False otherwise.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_handle_log_record&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Handle LogEvent and export to OTel logs.

  Converts Phlo log events to OpenTelemetry LogRecord format and emits
  to the configured log exporter. Preserves trace context from correlation
  or derives it from run\_id.

  Side Effects:

  * Emits LogRecord to OTel log emitter if configured

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    If log emitter is not configured (logs export disabled),
    this method silently returns without emitting.
  </Callout>

  <PySourceCode>
    ```python
    def _handle_log_record(self, event: Any) -> None:
        """Handle LogEvent and export to OTel logs.

                Converts Phlo log events to OpenTelemetry LogRecord format and emits
        to the configured log exporter. Preserves trace context from correlation
        or derives it from run_id.

        Args:
                    event: The LogEvent to process. Expected to have timestamp,
                        level, message, service, and metadata.

                Side Effects:
                    - Emits LogRecord to OTel log emitter if configured

        Note:
                    If log emitter is not configured (logs export disabled),
                    this method silently returns without emitting.

        """
        if not isinstance(event, LogEvent):
            return

        attributes = self._build_log_attributes(event)
        trace_id, span_id, trace_flags = self._resolve_log_context(event)
        log_record = LogRecord(
            timestamp=self._datetime_to_unix_nanos(event.timestamp),
            observed_timestamp=self._datetime_to_unix_nanos(datetime.now(event.timestamp.tzinfo)),
            trace_id=trace_id,
            span_id=span_id,
            trace_flags=trace_flags,
            severity_text=event.level.upper(),
            severity_number=self._map_severity(event.level),
            body=event.message,
            attributes=attributes,
        )
        emitter = get_log_emitter()
        if emitter is None:
            return
        emitter.emit(log_record)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The LogEvent to process. Expected to have timestamp,
      level, message, service, and metadata.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_get_counter&#x22;" type="&#x22;(self, name, *, description, unit='') -> Any&#x22;">
  Get or create a counter instrument with caching.

  <PySourceCode>
    ```python
    def _get_counter(self, name: str, *, description: str, unit: str = "") -> Any:
        """Get or create a counter instrument with caching.

        Args:
            name: The metric name.
            description: Human-readable description of the metric.
            unit: Unit of measurement (default: empty string).

        Returns:
            Counter: Cached or newly created counter instrument.

        """
        cache_key = (name, unit)
        counter = self._counter_cache.get(cache_key)
        if counter is None:
            counter = get_meter().create_counter(name, unit=unit, description=description)
            self._counter_cache[cache_key] = counter
        return counter
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      The metric name.
    </PyParameter>

    <PyParameter name="&#x22;description&#x22;" type="&#x22;str&#x22;" value="undefined">
      Human-readable description of the metric.
    </PyParameter>

    <PyParameter name="&#x22;unit&#x22;" type="&#x22;str&#x22;" value="&#x22;''&#x22;">
      Unit of measurement (default: empty string).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Cached or newly created counter instrument.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_gauge&#x22;" type="&#x22;(self, name, *, unit, description) -> Any&#x22;">
  Get or create a gauge instrument with caching.

  <PySourceCode>
    ```python
    def _get_gauge(self, name: str, *, unit: str, description: str) -> Any:
        """Get or create a gauge instrument with caching.

        Args:
            name: The metric name.
            unit: Unit of measurement.
            description: Human-readable description of the metric.

        Returns:
            Gauge: Cached or newly created gauge instrument.

        """
        cache_key = (name, unit)
        gauge = self._gauge_cache.get(cache_key)
        if gauge is None:
            gauge = get_meter().create_gauge(name, unit=unit, description=description)
            self._gauge_cache[cache_key] = gauge
        return gauge
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      The metric name.
    </PyParameter>

    <PyParameter name="&#x22;unit&#x22;" type="&#x22;str&#x22;" value="undefined">
      Unit of measurement.
    </PyParameter>

    <PyParameter name="&#x22;description&#x22;" type="&#x22;str&#x22;" value="undefined">
      Human-readable description of the metric.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Cached or newly created gauge instrument.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_histogram&#x22;" type="&#x22;(self, name, *, unit, description) -> Any&#x22;">
  Get or create a histogram instrument with caching.

  <PySourceCode>
    ```python
    def _get_histogram(self, name: str, *, unit: str, description: str) -> Any:
        """Get or create a histogram instrument with caching.

        Args:
            name: The metric name.
            unit: Unit of measurement.
            description: Human-readable description of the metric.

        Returns:
            Histogram: Cached or newly created histogram instrument.

        """
        cache_key = (name, unit)
        histogram = self._histogram_cache.get(cache_key)
        if histogram is None:
            histogram = get_meter().create_histogram(name, unit=unit, description=description)
            self._histogram_cache[cache_key] = histogram
        return histogram
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      The metric name.
    </PyParameter>

    <PyParameter name="&#x22;unit&#x22;" type="&#x22;str&#x22;" value="undefined">
      Unit of measurement.
    </PyParameter>

    <PyParameter name="&#x22;description&#x22;" type="&#x22;str&#x22;" value="undefined">
      Human-readable description of the metric.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Cached or newly created histogram instrument.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_up_down_counter&#x22;" type="&#x22;(self, name, *, unit, description) -> Any&#x22;">
  Get or create an up-down counter instrument with caching.

  <PySourceCode>
    ```python
    def _get_up_down_counter(self, name: str, *, unit: str, description: str) -> Any:
        """Get or create an up-down counter instrument with caching.

        Args:
            name: The metric name.
            unit: Unit of measurement.
            description: Human-readable description of the metric.

        Returns:
            UpDownCounter: Cached or newly created up-down counter instrument.

        """
        cache_key = (name, unit)
        counter = self._up_down_counter_cache.get(cache_key)
        if counter is None:
            counter = get_meter().create_up_down_counter(name, unit=unit, description=description)
            self._up_down_counter_cache[cache_key] = counter
        return counter
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      The metric name.
    </PyParameter>

    <PyParameter name="&#x22;unit&#x22;" type="&#x22;str&#x22;" value="undefined">
      Unit of measurement.
    </PyParameter>

    <PyParameter name="&#x22;description&#x22;" type="&#x22;str&#x22;" value="undefined">
      Human-readable description of the metric.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Cached or newly created up-down counter instrument.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_resolve_metric_kind&#x22;" type="&#x22;(self, payload) -> str&#x22;">
  Resolve telemetry metric type from reserved payload attributes.

  <PySourceCode>
    ```python
    def _resolve_metric_kind(self, payload: dict[str, Any]) -> str:
        """Resolve telemetry metric type from reserved payload attributes.

        Args:
            payload: Telemetry event payload dictionary.

        Returns:
            str: One of "counter", "gauge", "histogram", "up_down_counter".
                Defaults to "gauge" if not specified or invalid.

        """
        raw_kind = payload.get("metric_kind", payload.get("otel_metric_kind", "gauge"))
        if not isinstance(raw_kind, str):
            return "gauge"

        metric_kind = raw_kind.strip().lower().replace("-", "_")
        valid_kinds = {"counter", "gauge", "histogram", "up_down_counter"}
        if metric_kind not in valid_kinds:
            return "gauge"
        return metric_kind
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;payload&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Telemetry event payload dictionary.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    One of "counter", "gauge", "histogram", "up\_down\_counter".
    Defaults to "gauge" if not specified or invalid.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_normalize_metric_attributes&#x22;" type="&#x22;(self, payload) -> dict[str, Any]&#x22;">
  Normalize telemetry payload attributes for metrics.

  Filters payload to only allowed metric label keys and coerces
  values to valid metric attribute types.

  <PySourceCode>
    ```python
    def _normalize_metric_attributes(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Normalize telemetry payload attributes for metrics.

        Filters payload to only allowed metric label keys and coerces
        values to valid metric attribute types.

        Args:
            payload: Raw telemetry payload dictionary.

        Returns:
            dict[str, Any]: Filtered and coerced attributes suitable for
                metric dimensions.

        """
        normalized: dict[str, Any] = {}
        for key, value in payload.items():
            if key not in self._allowed_metric_label_keys():
                continue
            normalized[key] = self._coerce_metric_attribute_value(value)
        return normalized
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;payload&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Raw telemetry payload dictionary.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, Any]: Filtered and coerced attributes suitable for
    metric dimensions.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_set_numeric_span_attributes&#x22;" type="&#x22;(self, span, metrics) -> None&#x22;">
  Set numeric metrics as span attributes.

  <PySourceCode>
    ```python
    def _set_numeric_span_attributes(self, span: Span, metrics: dict[str, Any]) -> None:
        """Set numeric metrics as span attributes.

        Args:
            span: The span to set attributes on.
            metrics: Dictionary of metric name to numeric value.

        """
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                span.set_attribute(f"phlo.metrics.{key}", value)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;span&#x22;" type="&#x22;Span&#x22;" value="undefined">
      The span to set attributes on.
    </PyParameter>

    <PyParameter name="&#x22;metrics&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Dictionary of metric name to numeric value.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_set_event_tags&#x22;" type="&#x22;(self, span, tags) -> None&#x22;">
  Set event tags as span attributes with phlo.tags prefix.

  <PySourceCode>
    ```python
    def _set_event_tags(self, span: Span, tags: dict[str, str]) -> None:
        """Set event tags as span attributes with phlo.tags prefix.

        Args:
            span: The span to set attributes on.
            tags: Dictionary of tag key-value pairs.

        """
        for key, value in tags.items():
            span.set_attribute(f"phlo.tags.{key}", value)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;span&#x22;" type="&#x22;Span&#x22;" value="undefined">
      The span to set attributes on.
    </PyParameter>

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="undefined">
      Dictionary of tag key-value pairs.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_set_correlation_attributes&#x22;" type="&#x22;(self, span, correlation) -> None&#x22;">
  Set correlation attributes on a span.

  <PySourceCode>
    ```python
    def _set_correlation_attributes(self, span: Span, correlation: HookCorrelation) -> None:
        """Set correlation attributes on a span.

        Args:
            span: The span to set attributes on.
            correlation: HookCorrelation with request_id, run_id, asset_key, etc.

        """
        if correlation.request_id:
            span.set_attribute("phlo.request_id", correlation.request_id)
        if correlation.run_id:
            span.set_attribute("phlo.run_id", correlation.run_id)
        if correlation.asset_key:
            span.set_attribute("phlo.asset_key", correlation.asset_key)
        if correlation.job_name:
            span.set_attribute("phlo.job_name", correlation.job_name)
        if correlation.partition_key:
            span.set_attribute("phlo.partition_key", correlation.partition_key)
        if correlation.check_name:
            span.set_attribute("phlo.check_name", correlation.check_name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;span&#x22;" type="&#x22;Span&#x22;" value="undefined">
      The span to set attributes on.
    </PyParameter>

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="undefined">
      HookCorrelation with request\_id, run\_id, asset\_key, etc.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_set_attribute_if_present&#x22;" type="&#x22;(self, span, key, value) -> None&#x22;">
  Set a span attribute only if value is present and non-empty.

  <PySourceCode>
    ```python
    def _set_attribute_if_present(self, span: Span, key: str, value: str | None) -> None:
        """Set a span attribute only if value is present and non-empty.

        Args:
            span: The span to set attribute on.
            key: The attribute key.
            value: The attribute value (set only if truthy).

        """
        if value:
            span.set_attribute(key, value)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;span&#x22;" type="&#x22;Span&#x22;" value="undefined">
      The span to set attribute on.
    </PyParameter>

    <PyParameter name="&#x22;key&#x22;" type="&#x22;str&#x22;" value="undefined">
      The attribute key.
    </PyParameter>

    <PyParameter name="&#x22;value&#x22;" type="&#x22;str | None&#x22;" value="undefined">
      The attribute value (set only if truthy).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_metric_attributes_from_tags&#x22;" type="&#x22;(self, tags) -> dict[str, str]&#x22;">
  Extract allowed metric label keys from tags.

  <PySourceCode>
    ```python
    def _metric_attributes_from_tags(self, tags: dict[str, str]) -> dict[str, str]:
        """Extract allowed metric label keys from tags.

        Args:
            tags: Dictionary of tag key-value pairs.

        Returns:
            dict[str, str]: Filtered tags containing only allowed metric labels.

        """
        return {
            key: value for key, value in tags.items() if key in self._allowed_metric_label_keys()
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="undefined">
      Dictionary of tag key-value pairs.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, str]: Filtered tags containing only allowed metric labels.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_allowed_metric_label_keys&#x22;" type="&#x22;(self) -> set[str]&#x22;">
  Return the set of allowed metric label keys.

  These keys are allowed as metric dimensions to prevent high-cardinality
  issues while still providing useful filtering capabilities.

  <PySourceCode>
    ```python
    def _allowed_metric_label_keys(self) -> set[str]:
        """Return the set of allowed metric label keys.

        These keys are allowed as metric dimensions to prevent high-cardinality
        issues while still providing useful filtering capabilities.

        Returns:
            set[str]: Set of allowed metric attribute keys.

        """
        return {
            "backend",
            "classification",
            "environment",
            "namespace",
            "operation",
            "phase",
            "result",
            "service",
            "source",
            "source_type",
            "status",
            "target",
            "target_system",
            "tool",
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;set&#x22;">
    set\[str]: Set of allowed metric attribute keys.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_build_log_attributes&#x22;" type="&#x22;(self, event) -> dict[str, Any]&#x22;">
  Build OTel log attributes from a LogEvent.

  <PySourceCode>
    ```python
    def _build_log_attributes(self, event: LogEvent) -> dict[str, Any]:
        """Build OTel log attributes from a LogEvent.

        Args:
            event: The LogEvent to convert.

        Returns:
            dict[str, Any]: Dictionary of OTel log attributes including
                phlo-specific metadata and event tags.

        """
        correlation = self._merge_correlation(
            event.correlation,
            run_id=event.run_id,
            asset_key=event.asset_key,
            job_name=event.job_name,
            partition_key=event.partition_key,
            check_name=event.check_name,
        )
        attributes: dict[str, Any] = {
            "phlo.event_type": event.event_type,
            "phlo.stage": self._event_stage(event.event_type),
            "phlo.logger": event.logger,
            "phlo.level": event.level,
        }
        if event.service:
            attributes["phlo.service"] = event.service
            attributes["phlo.system"] = event.service
        operation = event.tags.get("operation")
        if operation:
            attributes["phlo.operation"] = operation
        if correlation.request_id:
            attributes["phlo.request_id"] = correlation.request_id
        if correlation.run_id:
            attributes["phlo.run_id"] = correlation.run_id
        if correlation.asset_key:
            attributes["phlo.asset_key"] = correlation.asset_key
        if correlation.job_name:
            attributes["phlo.job_name"] = correlation.job_name
        if correlation.partition_key:
            attributes["phlo.partition_key"] = correlation.partition_key
        if correlation.check_name:
            attributes["phlo.check_name"] = correlation.check_name

        for key, value in event.tags.items():
            attributes[f"phlo.tag.{key}"] = value
        for key, value in event.metadata.items():
            attributes[f"phlo.metadata.{key}"] = self._coerce_attribute_value(value)
        return attributes
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;LogEvent&#x22;" value="undefined">
      The LogEvent to convert.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, Any]: Dictionary of OTel log attributes including
    phlo-specific metadata and event tags.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_coerce_attribute_value&#x22;" type="&#x22;(self, value) -> Any&#x22;">
  Coerce a value to a valid OTel attribute type.

  OTel attributes must be primitive types (bool, int, float, str) or
  homogeneous lists of primitives.

  <PySourceCode>
    ```python
    def _coerce_attribute_value(self, value: Any) -> Any:
        """Coerce a value to a valid OTel attribute type.

        OTel attributes must be primitive types (bool, int, float, str) or
        homogeneous lists of primitives.

        Args:
            value: The value to coerce.

        Returns:
            Any: Coerced value suitable for OTel attributes.

        """
        if isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (list, tuple)):
            return [
                item if isinstance(item, (bool, int, float, str)) else str(item) for item in value
            ]
        return str(value)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The value to coerce.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Coerced value suitable for OTel attributes.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_coerce_metric_attribute_value&#x22;" type="&#x22;(self, value) -> Any&#x22;">
  Coerce a value to a valid metric attribute type.

  Similar to \_coerce\_attribute\_value but returns tuples for lists
  to ensure immutability for metric dimensions.

  <PySourceCode>
    ```python
    def _coerce_metric_attribute_value(self, value: Any) -> Any:
        """Coerce a value to a valid metric attribute type.

        Similar to _coerce_attribute_value but returns tuples for lists
        to ensure immutability for metric dimensions.

        Args:
            value: The value to coerce.

        Returns:
            Any: Coerced value suitable for metric attributes.

        """
        if isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (list, tuple)):
            return tuple(
                item if isinstance(item, (bool, int, float, str)) else str(item) for item in value
            )
        return str(value)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The value to coerce.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Coerced value suitable for metric attributes.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_map_severity&#x22;" type="&#x22;(self, level) -> SeverityNumber&#x22;">
  Map log level string to OTel SeverityNumber.

  <PySourceCode>
    ```python
    def _map_severity(self, level: str) -> SeverityNumber:
        """Map log level string to OTel SeverityNumber.

        Args:
            level: Log level string (debug, info, warning, error, critical, etc.)

        Returns:
            SeverityNumber: OTel severity number. Defaults to INFO for unknown levels.

        """
        normalized = level.strip().lower()
        if normalized == "debug":
            return SeverityNumber.DEBUG
        if normalized in {"warning", "warn"}:
            return SeverityNumber.WARN
        if normalized == "error":
            return SeverityNumber.ERROR
        if normalized == "critical":
            return SeverityNumber.FATAL
        return SeverityNumber.INFO
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;level&#x22;" type="&#x22;str&#x22;" value="undefined">
      Log level string (debug, info, warning, error, critical, etc.)
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;opentelemetry._logs.SeverityNumber&#x22;">
    OTel severity number. Defaults to INFO for unknown levels.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_event_stage&#x22;" type="&#x22;(self, event_type) -> str&#x22;">
  Determine the pipeline stage from event type.

  <PySourceCode>
    ```python
    def _event_stage(self, event_type: str) -> str:
        """Determine the pipeline stage from event type.

        Args:
            event_type: The event type string (e.g., "ingestion.complete").

        Returns:
            str: The pipeline stage (ingestion, transform, quality, lineage,
                publish, service, migration, telemetry, log).

        """
        prefix = event_type.split(".", maxsplit=1)[0]
        if prefix in {"schema_migration", "data_migration"}:
            return "migration"
        if prefix == "service":
            return "service"
        if prefix == "telemetry":
            return "telemetry"
        if prefix == "log":
            return "log"
        return prefix
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event_type&#x22;" type="&#x22;str&#x22;" value="undefined">
      The event type string (e.g., "ingestion.complete").
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    The pipeline stage (ingestion, transform, quality, lineage,
    publish, service, migration, telemetry, log).
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_is_failure_status&#x22;" type="&#x22;(self, status) -> bool&#x22;">
  Check if a status string indicates failure.

  <PySourceCode>
    ```python
    def _is_failure_status(self, status: str) -> bool:
        """Check if a status string indicates failure.

        Args:
            status: The status string to check.

        Returns:
            bool: True if status indicates an error/failure state.

        """
        return status.lower() in {"error", "failed", "failure", "rejected"}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="undefined">
      The status string to check.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if status indicates an error/failure state.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_record_duration&#x22;" type="&#x22;(self, metric_name, *, metrics, attributes, description) -> None&#x22;">
  Record duration metric from event metrics if available.

  <PySourceCode>
    ```python
    def _record_duration(
        self,
        metric_name: str,
        *,
        metrics: dict[str, Any],
        attributes: dict[str, str],
        description: str,
    ) -> None:
        """Record duration metric from event metrics if available.

        Args:
            metric_name: The name of the duration histogram.
            metrics: Event metrics dictionary containing duration.
            attributes: Metric attributes/dimensions.
            description: Metric description.

        """
        duration = self._extract_duration_seconds(metrics)
        if duration is None:
            return

        histogram = self._get_histogram(metric_name, unit="s", description=description)
        histogram.record(duration, attributes)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;metric_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      The name of the duration histogram.
    </PyParameter>

    <PyParameter name="&#x22;metrics&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Event metrics dictionary containing duration.
    </PyParameter>

    <PyParameter name="&#x22;attributes&#x22;" type="&#x22;dict[str, str]&#x22;" value="undefined">
      Metric attributes/dimensions.
    </PyParameter>

    <PyParameter name="&#x22;description&#x22;" type="&#x22;str&#x22;" value="undefined">
      Metric description.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_extract_duration_seconds&#x22;" type="&#x22;(self, metrics) -> float | None&#x22;">
  Extract duration in seconds from metrics dictionary.

  <PySourceCode>
    ```python
    def _extract_duration_seconds(self, metrics: dict[str, Any]) -> float | None:
        """Extract duration in seconds from metrics dictionary.

        Args:
            metrics: Dictionary of metric key-value pairs.

        Returns:
            float | None: Duration in seconds if found, None otherwise.

        """
        for key in ("duration_seconds", "total_elapsed_seconds", "elapsed_seconds"):
            value = metrics.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;metrics&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Dictionary of metric key-value pairs.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;float | None&#x22;">
    float | None: Duration in seconds if found, None otherwise.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_record_failure&#x22;" type="&#x22;(self, *, event_name, status, error=None) -> None&#x22;">
  Record failure/error counter if event indicates failure.

  <PySourceCode>
    ```python
    def _record_failure(
        self,
        *,
        event_name: str,
        status: str | None,
        error: str | None = None,
    ) -> None:
        """Record failure/error counter if event indicates failure.

        Args:
            event_name: Name of the event type for the error label.
            status: Event status string (checked for failure indicators).
            error: Optional error message (if present, counts as failure).

        """
        if not (error or (status and self._is_failure_status(status))):
            return

        counter = self._get_counter(
            "phlo.errors",
            description="Number of failed Phlo workflow events",
        )
        counter.add(1, {"event": event_name, "status": status or "error"})
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of the event type for the error label.
    </PyParameter>

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str | None&#x22;" value="undefined">
      Event status string (checked for failure indicators).
    </PyParameter>

    <PyParameter name="&#x22;error&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional error message (if present, counts as failure).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_datetime_to_unix_nanos&#x22;" type="&#x22;(self, value) -> int&#x22;">
  Convert datetime to Unix nanoseconds timestamp.

  <PySourceCode>
    ```python
    def _datetime_to_unix_nanos(self, value: datetime) -> int:
        """Convert datetime to Unix nanoseconds timestamp.

        Args:
            value: Datetime to convert.

        Returns:
            int: Unix timestamp in nanoseconds.

        """
        return int(value.timestamp() * 1_000_000_000)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;value&#x22;" type="&#x22;datetime&#x22;" value="undefined">
      Datetime to convert.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;">
    Unix timestamp in nanoseconds.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_resolve_log_context&#x22;" type="&#x22;(self, event) -> tuple[int | None, int | None, Any | None]&#x22;">
  Resolve trace context for a log event.

  Attempts to extract trace\_id, span\_id, and trace\_flags from event
  correlation, metadata, or derives stable identifiers from run\_id.

  <PySourceCode>
    ```python
    def _resolve_log_context(self, event: LogEvent) -> tuple[int | None, int | None, Any | None]:
        """Resolve trace context for a log event.

        Attempts to extract trace_id, span_id, and trace_flags from event
        correlation, metadata, or derives stable identifiers from run_id.

        Args:
            event: The LogEvent to extract context from.

        Returns:
            tuple: (trace_id, span_id, trace_flags) where values may be None
                if context cannot be determined.

        """
        correlation = self._merge_correlation(
            event.correlation,
            trace_id=event.metadata.get("trace_id"),
            span_id=event.metadata.get("span_id"),
            trace_flags=event.metadata.get("trace_flags"),
            run_id=event.run_id,
            asset_key=event.asset_key,
            job_name=event.job_name,
            partition_key=event.partition_key,
            check_name=event.check_name,
        )
        span_context = get_current_span().get_span_context()
        trace_id = span_id = trace_flags = None
        if span_context.is_valid:
            trace_id = span_context.trace_id
            span_id = span_context.span_id
            trace_flags = span_context.trace_flags

        metadata_trace_id = self._parse_trace_identifier(correlation.trace_id)
        metadata_span_id = self._parse_trace_identifier(correlation.span_id)
        metadata_trace_flags = self._parse_trace_flags(correlation.trace_flags)
        if metadata_trace_id is not None:
            trace_id = metadata_trace_id
        if metadata_span_id is not None:
            span_id = metadata_span_id
        if metadata_trace_flags is not None:
            trace_flags = metadata_trace_flags
        if trace_id is None or span_id is None:
            synthetic_trace_id, synthetic_span_id = self._derive_trace_context_identifiers(
                correlation
            )
            if trace_id is None:
                trace_id = synthetic_trace_id
            if span_id is None:
                span_id = synthetic_span_id
            if trace_flags is None and synthetic_trace_id is not None:
                trace_flags = TraceFlags(0x01)
        return trace_id, span_id, trace_flags
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;LogEvent&#x22;" value="undefined">
      The LogEvent to extract context from.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;tuple&#x22;">
    (trace\_id, span\_id, trace\_flags) where values may be None
    if context cannot be determined.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_merge_correlation&#x22;" type="&#x22;(self, correlation, **overrides) -> HookCorrelation&#x22;">
  Merge override values into a HookCorrelation.

  <PySourceCode>
    ```python
    def _merge_correlation(self, correlation: HookCorrelation, **overrides: Any) -> HookCorrelation:
        """Merge override values into a HookCorrelation.

        Args:
            correlation: Base correlation object.
            **overrides: Keyword arguments to override in the correlation.

        Returns:
            HookCorrelation: New correlation with overrides applied.

        """
        merged = HookCorrelation(**vars(correlation))
        for key, value in overrides.items():
            if value is not None:
                setattr(merged, key, str(value))
        return merged
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="undefined">
      Base correlation object.
    </PyParameter>

    <PyParameter name="&#x22;overrides&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.hooks.events.HookCorrelation&#x22;">
    New correlation with overrides applied.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_build_parent_context&#x22;" type="&#x22;(self, correlation) -> Context | None&#x22;">
  Build OTel parent context from correlation for distributed tracing.

  Creates a SpanContext from correlation trace\_id/span\_id or derives
  stable identifiers from run\_id/request\_id for trace continuity.

  <PySourceCode>
    ```python
    def _build_parent_context(self, correlation: HookCorrelation) -> Context | None:
        """Build OTel parent context from correlation for distributed tracing.

        Creates a SpanContext from correlation trace_id/span_id or derives
        stable identifiers from run_id/request_id for trace continuity.

        Args:
            correlation: HookCorrelation with trace context information.

        Returns:
            Context | None: OTel context with parent span, or None if no
                valid context can be constructed.

        """
        trace_id = self._parse_trace_identifier(correlation.trace_id)
        span_id = self._parse_trace_identifier(correlation.span_id)
        if trace_id is None or span_id is None:
            synthetic_trace_id, synthetic_span_id = self._derive_trace_context_identifiers(
                correlation
            )
            if trace_id is None:
                trace_id = synthetic_trace_id
            if span_id is None:
                span_id = synthetic_span_id
        if trace_id is None or span_id is None:
            return None

        trace_flags = self._parse_trace_flags(correlation.trace_flags) or TraceFlags(0x01)
        span_context = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            is_remote=True,
            trace_flags=trace_flags,
            trace_state=TraceState(),
        )
        return set_span_in_context(NonRecordingSpan(span_context))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="undefined">
      HookCorrelation with trace context information.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;Context | None&#x22;">
    Context | None: OTel context with parent span, or None if no
    valid context can be constructed.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_derive_trace_context_identifiers&#x22;" type="&#x22;(self, correlation) -> tuple[int | None, int | None]&#x22;">
  Derive stable trace\_id and span\_id from correlation.

  Uses run\_id or request\_id to generate deterministic trace identifiers,
  enabling trace continuity across process boundaries without explicit
  trace context propagation.

  <PySourceCode>
    ```python
    def _derive_trace_context_identifiers(
        self,
        correlation: HookCorrelation,
    ) -> tuple[int | None, int | None]:
        """Derive stable trace_id and span_id from correlation.

        Uses run_id or request_id to generate deterministic trace identifiers,
        enabling trace continuity across process boundaries without explicit
        trace context propagation.

        Args:
            correlation: HookCorrelation with run_id or request_id.

        Returns:
            tuple: (trace_id, span_id) as integers, or (None, None) if
                no grouping key is available.

        """
        grouping_key = self._trace_grouping_key(correlation)
        if grouping_key is None:
            return None, None

        trace_id = self._stable_identifier(f"trace:{grouping_key}", bytes_length=16)
        span_id = self._stable_identifier(f"span:{grouping_key}", bytes_length=8)
        return trace_id, span_id
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="undefined">
      HookCorrelation with run\_id or request\_id.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;tuple&#x22;">
    (trace\_id, span\_id) as integers, or (None, None) if
    no grouping key is available.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_trace_grouping_key&#x22;" type="&#x22;(self, correlation) -> str | None&#x22;">
  Determine the trace grouping key from correlation.

  <PySourceCode>
    ```python
    def _trace_grouping_key(self, correlation: HookCorrelation) -> str | None:
        """Determine the trace grouping key from correlation.

        Args:
            correlation: HookCorrelation with run_id and request_id.

        Returns:
            str | None: Grouping key for trace derivation, or None if neither
                run_id nor request_id is available.

        """
        if correlation.run_id:
            return f"run:{correlation.run_id}"
        if correlation.request_id:
            return f"request:{correlation.request_id}"
        return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="undefined">
      HookCorrelation with run\_id and request\_id.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;">
    str | None: Grouping key for trace derivation, or None if neither
    run\_id nor request\_id is available.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_stable_identifier&#x22;" type="&#x22;(self, value, *, bytes_length) -> int&#x22;">
  Generate a stable integer identifier from a string value.

  Uses SHA-256 hash to create deterministic identifiers for consistent
  trace context across distributed components processing the same event.

  <PySourceCode>
    ```python
    def _stable_identifier(self, value: str, *, bytes_length: int) -> int:
        """Generate a stable integer identifier from a string value.

        Uses SHA-256 hash to create deterministic identifiers for consistent
        trace context across distributed components processing the same event.

        Args:
            value: The string value to hash.
            bytes_length: Number of bytes to use from the hash (8 for span_id,
                16 for trace_id).

        Returns:
            int: Stable integer identifier derived from the hash.

        """
        digest = hashlib.sha256(value.encode("utf-8")).digest()
        return int.from_bytes(digest[:bytes_length], byteorder="big", signed=False)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;value&#x22;" type="&#x22;str&#x22;" value="undefined">
      The string value to hash.
    </PyParameter>

    <PyParameter name="&#x22;bytes_length&#x22;" type="&#x22;int&#x22;" value="undefined">
      Number of bytes to use from the hash (8 for span\_id,
      16 for trace\_id).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;">
    Stable integer identifier derived from the hash.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_parse_trace_identifier&#x22;" type="&#x22;(self, value) -> int | None&#x22;">
  Parse a trace identifier from various input formats.

  Handles hex strings (with or without 0x prefix), integers, and None.

  <PySourceCode>
    ```python
    def _parse_trace_identifier(self, value: Any) -> int | None:
        """Parse a trace identifier from various input formats.

        Handles hex strings (with or without 0x prefix), integers, and None.

        Args:
            value: The value to parse (str, int, or None).

        Returns:
            int | None: Parsed trace identifier, or None if parsing fails
                or value is None/empty.

        """
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if not isinstance(value, str):
            return None

        raw = value.strip().lower()
        if not raw:
            return None
        try:
            if raw.startswith("0x"):
                return int(raw, 16)
            return int(raw, 16)
        except ValueError:
            return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The value to parse (str, int, or None).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;int | None&#x22;">
    int | None: Parsed trace identifier, or None if parsing fails
    or value is None/empty.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_parse_trace_flags&#x22;" type="&#x22;(self, value) -> TraceFlags | None&#x22;">
  Parse trace flags from a value.

  <PySourceCode>
    ```python
    def _parse_trace_flags(self, value: Any) -> TraceFlags | None:
        """Parse trace flags from a value.

        Args:
            value: The value to parse (str, int, or None).

        Returns:
            TraceFlags | None: Parsed trace flags, or None if parsing fails.

        """
        trace_flags = self._parse_trace_identifier(value)
        if trace_flags is None:
            return None
        return TraceFlags(trace_flags & 0xFF)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The value to parse (str, int, or None).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;TraceFlags | None&#x22;">
    TraceFlags | None: Parsed trace flags, or None if parsing fails.
  </PyFunctionReturn>
</PyFunction>
