"""OpenTelemetry instrumentation for Phlo hook events."""

from phlo_otel.provider import get_log_emitter, get_meter, get_tracer, shutdown_otel

__all__ = [
    "get_log_emitter",
    "get_tracer",
    "get_meter",
    "shutdown_otel",
]
