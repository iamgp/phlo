"""Tests for the OTel provider resource configuration."""

from __future__ import annotations

from types import SimpleNamespace

from phlo_otel import provider


def test_build_resource_attributes(monkeypatch):
    monkeypatch.setenv("OTEL_SERVICE_NAME", "phlo-api")
    monkeypatch.setenv("OTEL_SERVICE_NAMESPACE", "phlohouse")
    monkeypatch.setenv("OTEL_SERVICE_VERSION", "1.2.3")
    monkeypatch.setenv("OTEL_SERVICE_INSTANCE_ID", "instance-7")
    monkeypatch.setenv("PHLO_PROJECT", "demo-lakehouse")
    monkeypatch.setattr(
        "phlo_otel.provider.get_settings",
        lambda: SimpleNamespace(
            phlo_environment="prod",
            phlo_log_service_name="ignored",
            phlo_service_namespace="ignored-namespace",
            phlo_service_version="ignored-version",
            phlo_service_instance_id="ignored-instance",
            phlo_project="ignored-project",
        ),
    )

    resource_attributes = provider._build_resource_attributes()

    assert resource_attributes["service.name"] == "phlo-api"
    assert resource_attributes["service.namespace"] == "phlohouse"
    assert resource_attributes["service.version"] == "1.2.3"
    assert resource_attributes["service.instance.id"] == "instance-7"
    assert resource_attributes["deployment.environment"] == "prod"
    assert resource_attributes["phlo.package"] == "phlo-otel"
    assert resource_attributes["phlo.runtime"] == "python"
    assert resource_attributes["phlo.project"] == "demo-lakehouse"


def test_build_resource_attributes_uses_phlo_defaults(monkeypatch):
    monkeypatch.delenv("OTEL_SERVICE_NAME", raising=False)
    monkeypatch.delenv("OTEL_SERVICE_NAMESPACE", raising=False)
    monkeypatch.delenv("OTEL_SERVICE_VERSION", raising=False)
    monkeypatch.delenv("OTEL_SERVICE_INSTANCE_ID", raising=False)
    monkeypatch.delenv("PHLO_PROJECT", raising=False)
    monkeypatch.setattr(
        "phlo_otel.provider.get_settings",
        lambda: SimpleNamespace(
            phlo_environment="dev",
            phlo_log_service_name="phlo-worker",
            phlo_service_namespace="phlo",
            phlo_service_version=None,
            phlo_service_instance_id=None,
            phlo_project=None,
        ),
    )
    monkeypatch.setattr("phlo_otel.provider.socket.gethostname", lambda: "worker-host")

    resource_attributes = provider._build_resource_attributes()

    assert resource_attributes["service.name"] == "phlo-worker"
    assert resource_attributes["service.namespace"] == "phlo"
    assert resource_attributes["service.version"] == provider.INSTRUMENTATION_VERSION
    assert resource_attributes["service.instance.id"] == "worker-host"
    assert resource_attributes["deployment.environment"] == "dev"
    assert resource_attributes["phlo.project"] == "phlo-worker"


def test_build_resource_attributes_uses_phlo_observability_settings(monkeypatch):
    monkeypatch.delenv("OTEL_SERVICE_NAME", raising=False)
    monkeypatch.delenv("OTEL_SERVICE_NAMESPACE", raising=False)
    monkeypatch.delenv("OTEL_SERVICE_VERSION", raising=False)
    monkeypatch.delenv("OTEL_SERVICE_INSTANCE_ID", raising=False)
    monkeypatch.delenv("PHLO_PROJECT", raising=False)
    monkeypatch.setattr(
        "phlo_otel.provider.get_settings",
        lambda: SimpleNamespace(
            phlo_environment="staging",
            phlo_log_service_name="phlo-api",
            phlo_service_namespace="lakehouse",
            phlo_service_version="2.4.0",
            phlo_service_instance_id="api-7",
            phlo_project="acme-analytics",
        ),
    )

    resource_attributes = provider._build_resource_attributes()

    assert resource_attributes["service.name"] == "phlo-api"
    assert resource_attributes["service.namespace"] == "lakehouse"
    assert resource_attributes["service.version"] == "2.4.0"
    assert resource_attributes["service.instance.id"] == "api-7"
    assert resource_attributes["deployment.environment"] == "staging"
    assert resource_attributes["phlo.project"] == "acme-analytics"


def test_get_log_emitter_uses_cached_logger_provider(monkeypatch):
    provider._initialized = True
    fake_logger = object()
    fake_provider = SimpleNamespace(get_logger=lambda name, version: fake_logger)
    monkeypatch.setattr(provider, "_logger_provider", fake_provider)

    assert provider.get_log_emitter() is fake_logger


def test_get_log_emitter_returns_none_when_logs_disabled(monkeypatch):
    monkeypatch.setattr(provider, "_initialized", True)
    monkeypatch.setattr(provider, "_logger_provider", None)

    assert provider.get_log_emitter() is None


def test_signal_export_enabled_defaults_off_without_endpoint(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", raising=False)
    monkeypatch.delenv("OTEL_TRACES_EXPORTER", raising=False)

    assert provider._traces_export_enabled() is False


def test_signal_export_enabled_uses_endpoint_when_exporter_unset(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4317")
    monkeypatch.delenv("OTEL_TRACES_EXPORTER", raising=False)

    assert provider._traces_export_enabled() is True


def test_shutdown_otel_resets_cached_providers(monkeypatch):
    calls: list[str] = []

    class FakeProvider:
        def __init__(self, name: str) -> None:
            self._name = name

        def shutdown(self) -> None:
            calls.append(self._name)

    monkeypatch.setattr(provider, "_initialized", True)
    monkeypatch.setattr(provider, "_logger_provider", FakeProvider("logs"))
    monkeypatch.setattr(provider, "_meter_provider", FakeProvider("metrics"))
    monkeypatch.setattr(provider, "_tracer_provider", FakeProvider("traces"))

    provider.shutdown_otel()

    assert calls == ["logs", "metrics", "traces"]
    assert provider._initialized is False
    assert provider._logger_provider is None
    assert provider._meter_provider is None
    assert provider._tracer_provider is None
