"""Grafana Alloy package for log collection and shipping to Loki.

This package provides integration with Grafana Alloy, a vendor-neutral OpenTelemetry
Collector distribution with built-in Prometheus pipelines and support for metrics,
logs, traces, and profiles. It includes the AlloyServicePlugin for service lifecycle
management within the Phlo platform.

Example:
    The package is auto-discovered via the ``phlo.services`` entry point and should
    not be imported directly by user code. Configuration is handled through the
    Alloy service plugin.

Attributes:
    __version__: Package version string.

Note:
    This package requires the ``phlo`` core to be installed for plugin registration.
    See https://grafana.com/docs/alloy/latest/ for Alloy documentation.

References:
    - Grafana Alloy: https://grafana.com/docs/alloy/latest/
    - OpenTelemetry Collector: https://opentelemetry.io/docs/collector/

"""

__version__ = "0.1.0"
