# provider (/docs/python-reference/packages/phlo-otel/phlo_otel/provider)



OTel TracerProvider and MeterProvider setup.

Configured via standard OTEL\_\* environment variables:

* OTEL\_EXPORTER\_OTLP\_ENDPOINT (default: [http://localhost:4317](http://localhost:4317))
* OTEL\_SERVICE\_NAME (default: phlo)
* OTEL\_SERVICE\_NAMESPACE (default: phlo)
* OTEL\_SERVICE\_VERSION (default: package version)
* OTEL\_SERVICE\_INSTANCE\_ID (default: hostname)
* OTEL\_TRACES\_EXPORTER (default: unset; set to otlp or configure an OTLP endpoint)
* OTEL\_METRICS\_EXPORTER (default: unset; set to otlp or configure an OTLP endpoint)
* OTEL\_LOGS\_EXPORTER (default: none; set to otlp to enable OTLP log export)
* OTEL\_RESOURCE\_ATTRIBUTES

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;metrics&#x22;" type="null" value="&#x22;cast(Any, importlib.import_module('opentelemetry.metrics'))&#x22;" />

<PyAttribute name="&#x22;trace&#x22;" type="null" value="&#x22;cast(Any, importlib.import_module('opentelemetry.trace'))&#x22;" />

<PyAttribute name="&#x22;OTLPMetricExporter&#x22;" type="null" value="&#x22;cast(Any, importlib.import_module('opentelemetry.exporter.otlp.proto.grpc.metric_exporter')).OTLPMetricExporter&#x22;" />

<PyAttribute name="&#x22;OTLPLogExporter&#x22;" type="null" value="&#x22;cast(Any, importlib.import_module('opentelemetry.exporter.otlp.proto.grpc._log_exporter')).OTLPLogExporter&#x22;" />

<PyAttribute name="&#x22;OTLPSpanExporter&#x22;" type="null" value="&#x22;cast(Any, importlib.import_module('opentelemetry.exporter.otlp.proto.grpc.trace_exporter')).OTLPSpanExporter&#x22;" />

<PyAttribute name="&#x22;LoggerProvider&#x22;" type="null" value="&#x22;cast(Any, importlib.import_module('opentelemetry.sdk._logs')).LoggerProvider&#x22;" />

<PyAttribute name="&#x22;BatchLogRecordProcessor&#x22;" type="null" value="&#x22;cast(Any, importlib.import_module('opentelemetry.sdk._logs.export')).BatchLogRecordProcessor&#x22;" />

<PyAttribute name="&#x22;MeterProvider&#x22;" type="null" value="&#x22;cast(Any, importlib.import_module('opentelemetry.sdk.metrics')).MeterProvider&#x22;" />

<PyAttribute name="&#x22;PeriodicExportingMetricReader&#x22;" type="null" value="&#x22;cast(Any, importlib.import_module('opentelemetry.sdk.metrics.export')).PeriodicExportingMetricReader&#x22;" />

<PyAttribute name="&#x22;resources&#x22;" type="null" value="&#x22;cast(Any, importlib.import_module('opentelemetry.sdk.resources'))&#x22;" />

<PyAttribute name="&#x22;SERVICE_NAME&#x22;" type="null" value="&#x22;resources.SERVICE_NAME&#x22;" />

<PyAttribute name="&#x22;Resource&#x22;" type="null" value="&#x22;resources.Resource&#x22;" />

<PyAttribute name="&#x22;TracerProvider&#x22;" type="null" value="&#x22;cast(Any, importlib.import_module('opentelemetry.sdk.trace')).TracerProvider&#x22;" />

<PyAttribute name="&#x22;BatchSpanProcessor&#x22;" type="null" value="&#x22;cast(Any, importlib.import_module('opentelemetry.sdk.trace.export')).BatchSpanProcessor&#x22;" />

<PyAttribute name="&#x22;Meter&#x22;" type="null" value="&#x22;Any&#x22;" />

<PyAttribute name="&#x22;Tracer&#x22;" type="null" value="&#x22;Any&#x22;" />

<PyAttribute name="&#x22;INSTRUMENTATION_NAME&#x22;" type="null" value="&#x22;'phlo'&#x22;" />

<PyAttribute name="&#x22;INSTRUMENTATION_VERSION&#x22;" type="null" value="&#x22;'0.1.0'&#x22;" />

<PyAttribute name="&#x22;PACKAGE_NAME&#x22;" type="null" value="&#x22;'phlo-otel'&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_build_resource_attributes&#x22;" type="&#x22;() -> dict[str, str]&#x22;">
      Build OTel resource attributes for Phlo process metadata.

      Constructs resource attributes from environment variables and Phlo settings,
      following the OpenTelemetry resource semantic conventions.

      The following precedence is used:

      1. OTEL\_\* environment variables
      2. Phlo configuration settings
      3. Package defaults

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > attrs = \_build\_resource\_attributes()
        > > > attrs\["service.name"]
        > > > 'phlo'
      </Callout>

      <PySourceCode>
        ```python
        def _build_resource_attributes() -> dict[str, str]:
            """Build OTel resource attributes for Phlo process metadata.

            Constructs resource attributes from environment variables and Phlo settings,
            following the OpenTelemetry resource semantic conventions.

            The following precedence is used:
            1. OTEL_* environment variables
            2. Phlo configuration settings
            3. Package defaults

            Returns:
                dict[str, str]: Mapping of resource attribute names to values.
                Includes service.name, service.namespace, service.version,
                service.instance.id, deployment.environment, and phlo-specific attributes.

            Example:
                >>> attrs = _build_resource_attributes()
                >>> attrs["service.name"]
                'phlo'

            """
            settings = get_settings()
            service_name = os.environ.get("OTEL_SERVICE_NAME", settings.phlo_log_service_name)
            service_namespace = os.environ.get("OTEL_SERVICE_NAMESPACE", settings.phlo_service_namespace)
            service_version = os.environ.get(
                "OTEL_SERVICE_VERSION",
                settings.phlo_service_version or INSTRUMENTATION_VERSION,
            )
            service_instance_id = os.environ.get(
                "OTEL_SERVICE_INSTANCE_ID",
                settings.phlo_service_instance_id or socket.gethostname(),
            )
            project = os.environ.get("PHLO_PROJECT", settings.phlo_project or service_name)
            return {
                SERVICE_NAME: service_name,
                "service.namespace": service_namespace,
                "service.version": service_version,
                "service.instance.id": service_instance_id,
                "deployment.environment": settings.phlo_environment,
                "phlo.package": PACKAGE_NAME,
                "phlo.runtime": "python",
                "phlo.project": project,
            }
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        dict\[str, str]: Mapping of resource attribute names to values.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_logs_export_enabled&#x22;" type="&#x22;() -> bool&#x22;">
      Return whether OTLP log export is enabled for this process.

      Checks OTEL\_LOGS\_EXPORTER and OTEL\_EXPORTER\_OTLP\_LOGS\_ENDPOINT
      environment variables to determine if log export should be enabled.

      <PySourceCode>
        ```python
        def _logs_export_enabled() -> bool:
            """Return whether OTLP log export is enabled for this process.

            Checks OTEL_LOGS_EXPORTER and OTEL_EXPORTER_OTLP_LOGS_ENDPOINT
            environment variables to determine if log export should be enabled.

            Returns:
                bool: True if OTLP log export is enabled, False otherwise.

            """
            return _signal_export_enabled(
                exporter_env="OTEL_LOGS_EXPORTER",
                signal_endpoint_env="OTEL_EXPORTER_OTLP_LOGS_ENDPOINT",
                default_enabled=False,
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if OTLP log export is enabled, False otherwise.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_traces_export_enabled&#x22;" type="&#x22;() -> bool&#x22;">
      Return whether OTLP trace export is enabled for this process.

      Checks OTEL\_TRACES\_EXPORTER and OTEL\_EXPORTER\_OTLP\_TRACES\_ENDPOINT
      environment variables to determine if trace export should be enabled.

      <PySourceCode>
        ```python
        def _traces_export_enabled() -> bool:
            """Return whether OTLP trace export is enabled for this process.

            Checks OTEL_TRACES_EXPORTER and OTEL_EXPORTER_OTLP_TRACES_ENDPOINT
            environment variables to determine if trace export should be enabled.

            Returns:
                bool: True if OTLP trace export is enabled, False otherwise.

            """
            return _signal_export_enabled(
                exporter_env="OTEL_TRACES_EXPORTER",
                signal_endpoint_env="OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
                default_enabled=False,
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if OTLP trace export is enabled, False otherwise.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_metrics_export_enabled&#x22;" type="&#x22;() -> bool&#x22;">
      Return whether OTLP metrics export is enabled for this process.

      Checks OTEL\_METRICS\_EXPORTER and OTEL\_EXPORTER\_OTLP\_METRICS\_ENDPOINT
      environment variables to determine if metrics export should be enabled.

      <PySourceCode>
        ```python
        def _metrics_export_enabled() -> bool:
            """Return whether OTLP metrics export is enabled for this process.

            Checks OTEL_METRICS_EXPORTER and OTEL_EXPORTER_OTLP_METRICS_ENDPOINT
            environment variables to determine if metrics export should be enabled.

            Returns:
                bool: True if OTLP metrics export is enabled, False otherwise.

            """
            return _signal_export_enabled(
                exporter_env="OTEL_METRICS_EXPORTER",
                signal_endpoint_env="OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
                default_enabled=False,
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if OTLP metrics export is enabled, False otherwise.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_signal_export_enabled&#x22;" type="&#x22;(*, exporter_env, signal_endpoint_env, default_enabled=True) -> bool&#x22;">
      Return whether an OTLP signal should be exported.

      Generic function to check if a specific OTLP signal (traces, metrics, logs)
      should be exported based on environment configuration.

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        If the exporter environment variable is explicitly set to "none" or empty,
        export is disabled regardless of endpoint configuration.
      </Callout>

      <PySourceCode>
        ```python
        def _signal_export_enabled(
            *,
            exporter_env: str,
            signal_endpoint_env: str,
            default_enabled: bool = True,
        ) -> bool:
            """Return whether an OTLP signal should be exported.

            Generic function to check if a specific OTLP signal (traces, metrics, logs)
            should be exported based on environment configuration.

            Args:
                exporter_env: Name of the environment variable for the exporter setting
                    (e.g., "OTEL_TRACES_EXPORTER").
                signal_endpoint_env: Name of the environment variable for the signal-specific
                    endpoint (e.g., "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT").
                default_enabled: Default value if neither environment variable is set.
                    Defaults to True.

            Returns:
                bool: True if the signal export is enabled, False otherwise.

            Note:
                If the exporter environment variable is explicitly set to "none" or empty,
                export is disabled regardless of endpoint configuration.

            """
            exporter = os.environ.get(exporter_env)
            if exporter is not None:
                return exporter.strip().lower() not in {"", "none"}
            if os.environ.get(signal_endpoint_env) or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
                return True
            return default_enabled
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;exporter_env&#x22;" type="&#x22;str&#x22;" value="undefined">
          Name of the environment variable for the exporter setting
          (e.g., "OTEL\_TRACES\_EXPORTER").
        </PyParameter>

        <PyParameter name="&#x22;signal_endpoint_env&#x22;" type="&#x22;str&#x22;" value="undefined">
          Name of the environment variable for the signal-specific
          endpoint (e.g., "OTEL\_EXPORTER\_OTLP\_TRACES\_ENDPOINT").
        </PyParameter>

        <PyParameter name="&#x22;default_enabled&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Default value if neither environment variable is set.
          Defaults to True.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if the signal export is enabled, False otherwise.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_ensure_initialized&#x22;" type="&#x22;() -> None&#x22;">
      Set up global TracerProvider and MeterProvider once.

      Idempotent initialization of OpenTelemetry SDK components. Creates and configures
      the TracerProvider, MeterProvider, and LoggerProvider based on environment
      settings. Uses lazy initialization pattern - only runs once even if called
      multiple times.

      Providers are registered globally and will be flushed on process exit via
      the atexit handler registered with shutdown\_otel().

      Side Effects:

      * Sets global \_initialized flag to True
      * Configures opentelemetry.trace global tracer provider
      * Configures opentelemetry.metrics global meter provider
      * Logs initialization event with service metadata

      <PySourceCode>
        ```python
        def _ensure_initialized() -> None:
            """Set up global TracerProvider and MeterProvider once.

            Idempotent initialization of OpenTelemetry SDK components. Creates and configures
            the TracerProvider, MeterProvider, and LoggerProvider based on environment
            settings. Uses lazy initialization pattern - only runs once even if called
            multiple times.

            Providers are registered globally and will be flushed on process exit via
            the atexit handler registered with shutdown_otel().

            Side Effects:
                - Sets global _initialized flag to True
                - Configures opentelemetry.trace global tracer provider
                - Configures opentelemetry.metrics global meter provider
                - Logs initialization event with service metadata
            """
            global _initialized, _logger_provider, _meter_provider, _tracer_provider
            if _initialized:
                return

            resource_attributes = _build_resource_attributes()
            resource = Resource.create(resource_attributes)

            tracer_provider = None
            if _traces_export_enabled():
                tracer_provider = TracerProvider(resource=resource)
                tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
                trace.set_tracer_provider(tracer_provider)

            logger_provider = None
            if _logs_export_enabled():
                logger_provider = LoggerProvider(resource=resource)
                logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))

            meter_provider = None
            if _metrics_export_enabled():
                metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter())
                meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
                metrics.set_meter_provider(meter_provider)

            _logger_provider = logger_provider
            _tracer_provider = tracer_provider
            _meter_provider = meter_provider
            _initialized = True
            logger.info(
                "otel_initialized",
                service_name=resource_attributes[SERVICE_NAME],
                service_namespace=resource_attributes["service.namespace"],
                environment=resource_attributes["deployment.environment"],
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_tracer&#x22;" type="&#x22;() -> Tracer&#x22;">
      Return the Phlo OTel tracer.

      Returns a tracer instance for creating spans. If tracing is not enabled,
      returns a no-op tracer that creates non-recording spans.

      The tracer is lazily initialized - the first call will set up the
      TracerProvider if tracing is enabled.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > tracer = get\_tracer()
        > > > with tracer.start\_as\_current\_span("operation") as span:
        > > > ...     span.set\_attribute("key", "value")
      </Callout>

      <PySourceCode>
        ```python
        def get_tracer() -> Tracer:
            """Return the Phlo OTel tracer.

            Returns a tracer instance for creating spans. If tracing is not enabled,
            returns a no-op tracer that creates non-recording spans.

            The tracer is lazily initialized - the first call will set up the
            TracerProvider if tracing is enabled.

            Returns:
                Tracer: OpenTelemetry tracer instance configured for Phlo instrumentation.

            Example:
                >>> tracer = get_tracer()
                >>> with tracer.start_as_current_span("operation") as span:
                ...     span.set_attribute("key", "value")

            """
            if not _traces_export_enabled():
                return trace.get_tracer(INSTRUMENTATION_NAME, INSTRUMENTATION_VERSION)
            _ensure_initialized()
            return trace.get_tracer(INSTRUMENTATION_NAME, INSTRUMENTATION_VERSION)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_otel.provider.Tracer&#x22;">
        OpenTelemetry tracer instance configured for Phlo instrumentation.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_meter&#x22;" type="&#x22;() -> Meter&#x22;">
      Return the Phlo OTel meter.

      Returns a meter instance for creating and recording metrics. If metrics
      export is not enabled, returns a no-op meter that discards all recordings.

      The meter is lazily initialized - the first call will set up the
      MeterProvider if metrics export is enabled.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > meter = get\_meter()
        > > > counter = meter.create\_counter("events")
        > > > counter.add(1, \{"type": "ingestion"})
      </Callout>

      <PySourceCode>
        ```python
        def get_meter() -> Meter:
            """Return the Phlo OTel meter.

            Returns a meter instance for creating and recording metrics. If metrics
            export is not enabled, returns a no-op meter that discards all recordings.

            The meter is lazily initialized - the first call will set up the
            MeterProvider if metrics export is enabled.

            Returns:
                Meter: OpenTelemetry meter instance configured for Phlo instrumentation.

            Example:
                >>> meter = get_meter()
                >>> counter = meter.create_counter("events")
                >>> counter.add(1, {"type": "ingestion"})

            """
            if not _metrics_export_enabled():
                return metrics.get_meter(INSTRUMENTATION_NAME, INSTRUMENTATION_VERSION)
            _ensure_initialized()
            return metrics.get_meter(INSTRUMENTATION_NAME, INSTRUMENTATION_VERSION)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_otel.provider.Meter&#x22;">
        OpenTelemetry meter instance configured for Phlo instrumentation.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_log_emitter&#x22;" type="&#x22;() -> Any&#x22;">
      Return the Phlo OTel log emitter.

      Returns a logger instance for emitting structured log records to OTel.
      If log export is not enabled, returns None.

      The log emitter is lazily initialized - the first call will set up the
      LoggerProvider if log export is enabled.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > emitter = get\_log\_emitter()
        > > > if emitter:
        > > > ...     log\_record = LogRecord(
        > > > ...         timestamp=time\_ns(),
        > > > ...         severity\_text="INFO",
        > > > ...         body="Processing complete",
        > > > ...     )
        > > > ...     emitter.emit(log\_record)
      </Callout>

      <PySourceCode>
        ```python
        def get_log_emitter() -> Any:
            """Return the Phlo OTel log emitter.

            Returns a logger instance for emitting structured log records to OTel.
            If log export is not enabled, returns None.

            The log emitter is lazily initialized - the first call will set up the
            LoggerProvider if log export is enabled.

            Returns:
                Logger | None: OpenTelemetry logger instance if log export is enabled,
                    None otherwise.

            Example:
                >>> emitter = get_log_emitter()
                >>> if emitter:
                ...     log_record = LogRecord(
                ...         timestamp=time_ns(),
                ...         severity_text="INFO",
                ...         body="Processing complete",
                ...     )
                ...     emitter.emit(log_record)

            """
            _ensure_initialized()
            if _logger_provider is None:
                return None
            return _logger_provider.get_logger(INSTRUMENTATION_NAME, INSTRUMENTATION_VERSION)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;">
        Logger | None: OpenTelemetry logger instance if log export is enabled,
        None otherwise.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;shutdown_otel&#x22;" type="&#x22;() -> None&#x22;">
      Flush and stop OTel providers created by this module.

      Gracefully shuts down all initialized OpenTelemetry providers, flushing
      any pending telemetry data before shutdown. This function is automatically
      registered with atexit and will be called on normal process termination.

      After shutdown, all cached providers are cleared and the initialization
      state is reset, allowing re-initialization if needed.

      Side Effects:

      * Flushes pending spans, metrics, and logs
      * Shuts down TracerProvider, MeterProvider, and LoggerProvider
      * Clears internal provider references
      * Resets \_initialized flag to False

      Note:
      This function is safe to call multiple times. Subsequent calls are no-ops
      if providers are already shut down.

      <PySourceCode>
        ```python
        def shutdown_otel() -> None:
            """Flush and stop OTel providers created by this module.

            Gracefully shuts down all initialized OpenTelemetry providers, flushing
            any pending telemetry data before shutdown. This function is automatically
            registered with atexit and will be called on normal process termination.

            After shutdown, all cached providers are cleared and the initialization
            state is reset, allowing re-initialization if needed.

            Side Effects:
                - Flushes pending spans, metrics, and logs
                - Shuts down TracerProvider, MeterProvider, and LoggerProvider
                - Clears internal provider references
                - Resets _initialized flag to False

            Note:
                This function is safe to call multiple times. Subsequent calls are no-ops
                if providers are already shut down.

            """
            global _initialized, _logger_provider, _meter_provider, _tracer_provider

            for provider in (_logger_provider, _meter_provider, _tracer_provider):
                if provider is None or not _provider_needs_shutdown(provider):
                    continue
                shutdown = getattr(provider, "shutdown", None)
                if callable(shutdown):
                    shutdown()

            _logger_provider = None
            _meter_provider = None
            _tracer_provider = None
            _initialized = False
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_provider_needs_shutdown&#x22;" type="&#x22;(provider) -> bool&#x22;">
      Return whether an OTel provider still has active shutdown work.

      Checks various internal state attributes of OpenTelemetry providers to
      determine if they need to be shut down. Different provider implementations
      use different internal attribute names for tracking shutdown state.

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        This is an internal helper that inspects implementation-specific
        attributes and may need updates if OTel SDK internals change.
      </Callout>

      <PySourceCode>
        ```python
        def _provider_needs_shutdown(provider: Any) -> bool:
            """Return whether an OTel provider still has active shutdown work.

            Checks various internal state attributes of OpenTelemetry providers to
            determine if they need to be shut down. Different provider implementations
            use different internal attribute names for tracking shutdown state.

            Args:
                provider: OpenTelemetry provider instance (TracerProvider, MeterProvider,
                    or LoggerProvider).

            Returns:
                bool: True if the provider appears to be active and needs shutdown,
                    False if already shut down or in an unknown state.

            Note:
                This is an internal helper that inspects implementation-specific
                attributes and may need updates if OTel SDK internals change.

            """
            if hasattr(provider, "_shutdown"):
                return not bool(getattr(provider, "_shutdown"))
            if hasattr(provider, "_at_exit_handler"):
                return getattr(provider, "_at_exit_handler") is not None
            if hasattr(provider, "_atexit_handler"):
                return getattr(provider, "_atexit_handler") is not None
            return True
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;provider&#x22;" type="&#x22;Any&#x22;" value="undefined">
          OpenTelemetry provider instance (TracerProvider, MeterProvider,
          or LoggerProvider).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if the provider appears to be active and needs shutdown,
        False if already shut down or in an unknown state.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
