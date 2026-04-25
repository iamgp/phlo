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
_CLICKSTACK_QUERY_USER_ENV = "CLICKSTACK_QUERY_USER"
_CLICKSTACK_QUERY_PASSWORD_ENV = "CLICKSTACK_QUERY_PASSWORD"
_CLICKSTACK_HTTP_PORT_ENV = "CLICKSTACK_HTTP_PORT"
_DEFAULT_CLICKSTACK_HTTP_PORT = "8123"
_CONTAINER_CLICKSTACK_QUERY_URL = f"http://clickstack:{_DEFAULT_CLICKSTACK_HTTP_PORT}"


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
        response = requests.post(
            query_url,
            data=query.encode("utf-8"),
            auth=self._resolve_clickstack_query_auth(),
            timeout=10,
        )
        response.raise_for_status()
        spans: list[TraceSpan] = []
        for line in response.text.splitlines():
            if not line.strip():
                continue
            spans.append(TraceSpan(**json.loads(line)))
        return spans

    def _resolve_clickstack_query_url(self) -> str:
        query_url = os.environ.get(_CLICKSTACK_QUERY_URL_ENV)
        if query_url:
            return query_url.rstrip("/")
        if _running_in_container():
            return _CONTAINER_CLICKSTACK_QUERY_URL
        port = os.environ.get(_CLICKSTACK_HTTP_PORT_ENV, _DEFAULT_CLICKSTACK_HTTP_PORT)
        return f"http://127.0.0.1:{port}"

    def _resolve_clickstack_query_auth(self) -> tuple[str, str] | None:
        user = os.environ.get(_CLICKSTACK_QUERY_USER_ENV)
        password = os.environ.get(_CLICKSTACK_QUERY_PASSWORD_ENV)
        if user is None:
            return None
        return (user, password or "")


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


def _running_in_container() -> bool:
    return os.path.exists("/.dockerenv")
