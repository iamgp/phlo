"""ClickStack-backed observability capability provider."""

from __future__ import annotations

import json
import os

import requests

from phlo.capabilities import (
    CapabilitySupport,
    DefaultObservabilityBackend,
    ObservabilityBackendSpec,
    TraceSpan,
)

_CLICKSTACK_QUERY_URL_ENV = "CLICKSTACK_QUERY_URL"
_DEFAULT_CLICKSTACK_QUERY_URL = "http://clickstack:8123"


class ClickStackObservabilityBackend(DefaultObservabilityBackend):
    """Observability backend with OTEL span queries backed by ClickStack."""

    def run_trace_spans(self, run_id: str, limit: int = 500) -> list[TraceSpan]:
        query_url = self._resolve_clickstack_query_url()
        escaped_run_id = _escape_clickhouse_string(run_id)
        query = f"""
SELECT
    toString(Timestamp) AS timestamp,
    TraceId AS trace_id,
    SpanId AS span_id,
    nullIf(ParentSpanId, '') AS parent_span_id,
    SpanName AS span_name,
    ServiceName AS service_name,
    SpanKind AS span_kind,
    round(Duration / 1000000, 3) AS duration_ms,
    StatusCode AS status_code,
    SpanAttributes AS span_attributes,
    ResourceAttributes AS resource_attributes
FROM default.otel_traces
WHERE SpanAttributes['phlo.run_id'] = '{escaped_run_id}'
ORDER BY Timestamp ASC
LIMIT {limit}
FORMAT JSONEachRow
""".strip()
        response = requests.post(query_url, data=query.encode("utf-8"), timeout=10)
        response.raise_for_status()
        spans: list[TraceSpan] = []
        for line in response.text.splitlines():
            if not line.strip():
                continue
            spans.append(TraceSpan(**json.loads(line)))
        return spans

    def _resolve_clickstack_query_url(self) -> str:
        return os.environ.get(_CLICKSTACK_QUERY_URL_ENV, _DEFAULT_CLICKSTACK_QUERY_URL).rstrip("/")


def build_clickstack_observability_spec() -> ObservabilityBackendSpec:
    """Build the ClickStack observability capability spec."""
    return ObservabilityBackendSpec(
        name="default",
        provider=ClickStackObservabilityBackend(),
        metadata={
            "default_stack": ["phlo-otel", "phlo-clickstack"],
            "service_dependencies": ["clickstack"],
            "backend": "clickstack",
        },
        support=CapabilitySupport(
            supports_metrics=True,
            supports_logs=True,
            supports_dashboards=True,
            supports_alerts=True,
        ),
    )


def _escape_clickhouse_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")
