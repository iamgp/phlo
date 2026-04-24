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


def test_clickstack_backend_queries_trace_spans(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_post(url: str, data: bytes, timeout: int):  # noqa: ANN001
        captured["url"] = url
        captured["query"] = data.decode("utf-8")
        return _FakeResponse(
            '{"timestamp":"2026-01-01T00:00:00Z","trace_id":"abc123","span_id":"span-1","parent_span_id":null,"span_name":"materialize_orders","service_name":"dagster","span_kind":"INTERNAL","duration_ms":12.5,"status_code":"STATUS_CODE_OK","span_attributes":{"phlo.run_id":"run-123"},"resource_attributes":{"service.name":"dagster"}}\n'
        )

    monkeypatch.setattr("phlo_clickstack.observability_backend.requests.post", fake_post)
    monkeypatch.setenv("CLICKSTACK_QUERY_URL", "http://clickstack.test:8123")

    backend = ClickStackObservabilityBackend()
    spans = backend.run_trace_spans("run-123", limit=25)

    assert captured["url"] == "http://clickstack.test:8123"
    assert "otel_traces" in captured["query"]
    assert "run-123" in captured["query"]
    assert "LIMIT 25" in captured["query"]
    assert spans[0].trace_id == "abc123"
