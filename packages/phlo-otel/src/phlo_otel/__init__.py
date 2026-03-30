"""OpenTelemetry instrumentation for Phlo hook events.

This module provides the public API for the phlo-otel package, exposing
the core OpenTelemetry components (tracer, meter, log emitter) and lifecycle
management functions.

Example:
    from phlo_otel import get_tracer, get_meter

    tracer = get_tracer()
    meter = get_meter()

    with tracer.start_as_current_span("my_operation") as span:
        counter = meter.create_counter("operations")
        counter.add(1)

"""

from __future__ import annotations

from phlo_otel.provider import get_log_emitter, get_meter, get_tracer, shutdown_otel

__all__ = [
    "get_log_emitter",
    "get_tracer",
    "get_meter",
    "shutdown_otel",
]
