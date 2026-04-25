"""Tests for ClickStack observability backend capability."""

from __future__ import annotations

from phlo_clickstack.observability_backend import (
    ClickStackObservabilityBackend,
    build_clickstack_observability_spec,
)


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


def test_build_clickstack_observability_spec_uses_default_name() -> None:
    spec = build_clickstack_observability_spec()

    assert spec.name == "default"
    assert spec.metadata["backend"] == "clickstack"
    assert spec.support.supports_logs is True


def test_clickstack_backend_defaults_to_host_http_port(monkeypatch) -> None:
    monkeypatch.delenv("CLICKSTACK_QUERY_URL", raising=False)
    monkeypatch.delenv("CLICKSTACK_HTTP_PORT", raising=False)
    monkeypatch.setattr(
        "phlo_clickstack.observability_backend._running_in_container", lambda: False
    )

    backend = ClickStackObservabilityBackend()

    assert backend._resolve_clickstack_query_url() == "http://127.0.0.1:8123"


def test_clickstack_backend_uses_container_url_in_container(monkeypatch) -> None:
    monkeypatch.delenv("CLICKSTACK_QUERY_URL", raising=False)
    monkeypatch.setattr("phlo_clickstack.observability_backend._running_in_container", lambda: True)

    backend = ClickStackObservabilityBackend()

    assert backend._resolve_clickstack_query_url() == "http://clickstack:8123"


def test_clickstack_backend_queries_trace_spans(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, data: bytes, auth: tuple[str, str] | None, timeout: int):  # noqa: ANN001
        captured["url"] = url
        captured["query"] = data.decode("utf-8")
        captured["auth"] = auth
        return _FakeResponse(
            '{"timestamp":"2026-01-01T00:00:00Z","trace_id":"abc123","span_id":"span-1","parent_span_id":null,"span_name":"materialize_orders","service_name":"dagster","span_kind":"INTERNAL","duration_ms":12.5,"status_code":"STATUS_CODE_OK","span_attributes":{"phlo.run_id":"run-123"},"resource_attributes":{"service.name":"dagster"}}\n'
        )

    monkeypatch.setattr("phlo_clickstack.observability_backend.requests.post", fake_post)
    monkeypatch.setenv("CLICKSTACK_QUERY_URL", "http://clickstack.test:8123")
    monkeypatch.setenv("CLICKSTACK_QUERY_USER", "api")
    monkeypatch.setenv("CLICKSTACK_QUERY_PASSWORD", "api")

    backend = ClickStackObservabilityBackend()
    spans = backend.run_trace_spans("run-123", limit=25)

    assert captured["url"] == "http://clickstack.test:8123"
    assert "otel_traces" in captured["query"]
    assert "run-123" in captured["query"]
    assert "LIMIT 25" in captured["query"]
    assert captured["auth"] == ("api", "api")
    assert spans[0].trace_id == "abc123"
