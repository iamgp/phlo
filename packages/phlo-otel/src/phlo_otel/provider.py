"""OTel TracerProvider and MeterProvider setup.

Configured via standard OTEL_* environment variables:
- OTEL_EXPORTER_OTLP_ENDPOINT (default: http://localhost:4317)
- OTEL_SERVICE_NAME (default: phlo)
- OTEL_SERVICE_NAMESPACE (default: phlo)
- OTEL_SERVICE_VERSION (default: package version)
- OTEL_SERVICE_INSTANCE_ID (default: hostname)
- OTEL_TRACES_EXPORTER (default: unset; set to otlp or configure an OTLP endpoint)
- OTEL_METRICS_EXPORTER (default: unset; set to otlp or configure an OTLP endpoint)
- OTEL_LOGS_EXPORTER (default: none; set to otlp to enable OTLP log export)
- OTEL_RESOURCE_ATTRIBUTES
"""

from __future__ import annotations

import atexit
import os
import socket
from typing import Any

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.metrics import Meter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Tracer

from phlo.config import get_settings
from phlo.logging import get_logger

logger = get_logger(__name__)

_initialized = False
_logger_provider: LoggerProvider | None = None
_tracer_provider: TracerProvider | None = None
_meter_provider: MeterProvider | None = None

INSTRUMENTATION_NAME = "phlo"
INSTRUMENTATION_VERSION = "0.1.0"
PACKAGE_NAME = "phlo-otel"


def _build_resource_attributes() -> dict[str, str]:
    """Build OTel resource attributes for Phlo process metadata."""
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


def _logs_export_enabled() -> bool:
    """Return whether OTLP log export is enabled for this process."""
    return _signal_export_enabled(
        exporter_env="OTEL_LOGS_EXPORTER",
        signal_endpoint_env="OTEL_EXPORTER_OTLP_LOGS_ENDPOINT",
        default_enabled=False,
    )


def _traces_export_enabled() -> bool:
    """Return whether OTLP trace export is enabled for this process."""
    return _signal_export_enabled(
        exporter_env="OTEL_TRACES_EXPORTER",
        signal_endpoint_env="OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
        default_enabled=False,
    )


def _metrics_export_enabled() -> bool:
    """Return whether OTLP metrics export is enabled for this process."""
    return _signal_export_enabled(
        exporter_env="OTEL_METRICS_EXPORTER",
        signal_endpoint_env="OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
        default_enabled=False,
    )


def _signal_export_enabled(
    *,
    exporter_env: str,
    signal_endpoint_env: str,
    default_enabled: bool = True,
) -> bool:
    """Return whether an OTLP signal should be exported."""
    exporter = os.environ.get(exporter_env)
    if exporter is not None:
        return exporter.strip().lower() not in {"", "none"}
    if os.environ.get(signal_endpoint_env) or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return True
    return default_enabled


def _ensure_initialized() -> None:
    """Set up global TracerProvider and MeterProvider once."""
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


def get_tracer() -> Tracer:
    """Return the Phlo OTel tracer."""
    if not _traces_export_enabled():
        return trace.get_tracer(INSTRUMENTATION_NAME, INSTRUMENTATION_VERSION)
    _ensure_initialized()
    return trace.get_tracer(INSTRUMENTATION_NAME, INSTRUMENTATION_VERSION)


def get_meter() -> Meter:
    """Return the Phlo OTel meter."""
    if not _metrics_export_enabled():
        return metrics.get_meter(INSTRUMENTATION_NAME, INSTRUMENTATION_VERSION)
    _ensure_initialized()
    return metrics.get_meter(INSTRUMENTATION_NAME, INSTRUMENTATION_VERSION)


def get_log_emitter() -> Any:
    """Return the Phlo OTel log emitter."""
    _ensure_initialized()
    if _logger_provider is None:
        return None
    return _logger_provider.get_logger(INSTRUMENTATION_NAME, INSTRUMENTATION_VERSION)


def shutdown_otel() -> None:
    """Flush and stop OTel providers created by this module."""
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


def _provider_needs_shutdown(provider: Any) -> bool:
    """Return whether an OTel provider still has active shutdown work."""
    if hasattr(provider, "_shutdown"):
        return not bool(getattr(provider, "_shutdown"))
    if hasattr(provider, "_at_exit_handler"):
        return getattr(provider, "_at_exit_handler") is not None
    if hasattr(provider, "_atexit_handler"):
        return getattr(provider, "_atexit_handler") is not None
    return True


atexit.register(shutdown_otel)
