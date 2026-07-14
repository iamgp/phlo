from __future__ import annotations

from phlo.security.validation import run_regulated_validation


def test_regulated_validation_requires_audit_hmac_key(monkeypatch) -> None:
    monkeypatch.setenv("PHLO_REGULATED", "true")
    monkeypatch.delenv("PHLO_AUDIT_HMAC_KEY", raising=False)
    monkeypatch.delenv("PHLO_SIGNATURE_HMAC_KEY", raising=False)

    report = run_regulated_validation(surface_actions=[], surface_resource_types=[])

    check = next(item for item in report.checks if item.name == "compliance_hmac_keys_configured")
    assert check.passed is False
    assert "PHLO_AUDIT_HMAC_KEY is required" in check.message


def test_regulated_validation_requires_signature_hmac_key(monkeypatch) -> None:
    monkeypatch.setenv("PHLO_REGULATED", "true")
    monkeypatch.setenv("PHLO_AUDIT_HMAC_KEY", "test-audit-key")
    monkeypatch.delenv("PHLO_SIGNATURE_HMAC_KEY", raising=False)

    report = run_regulated_validation(surface_actions=[], surface_resource_types=[])

    check = next(item for item in report.checks if item.name == "compliance_hmac_keys_configured")
    assert check.passed is False
    assert "PHLO_SIGNATURE_HMAC_KEY is required" in check.message


def test_regulated_validation_accepts_configured_hmac_keys(monkeypatch) -> None:
    monkeypatch.setenv("PHLO_REGULATED", "true")
    monkeypatch.setenv("PHLO_AUDIT_HMAC_KEY", "test-audit-key")
    monkeypatch.setenv("PHLO_SIGNATURE_HMAC_KEY", "test-signature-key")

    report = run_regulated_validation(surface_actions=[], surface_resource_types=[])

    check = next(item for item in report.checks if item.name == "compliance_hmac_keys_configured")
    assert check.passed is True
    assert "audit and signature HMAC keys are configured" in check.message


def test_regulated_validation_rejects_arbitrary_identity_provider(monkeypatch) -> None:
    from phlo.security.validation import _check_identity_provider

    monkeypatch.setenv("PHLO_AUTHENTICATION_PROVIDER", "foo")

    result = _check_identity_provider()

    assert result.passed is False
    assert "Unsupported regulated identity provider" in result.message


def test_regulated_validation_rejects_missing_provider_settings(monkeypatch) -> None:
    from phlo.security.validation import _check_identity_provider

    monkeypatch.setenv("PHLO_AUTHENTICATION_PROVIDER", "proxy")
    monkeypatch.delenv("PHLO_AUTH_PROXY_SHARED_SECRET", raising=False)

    result = _check_identity_provider()

    assert result.passed is False
    assert "PHLO_AUTH_PROXY_SHARED_SECRET" in result.message


def test_regulated_validation_rejects_unregistered_provider(monkeypatch) -> None:
    from phlo.security.validation import _check_identity_provider

    monkeypatch.setenv("PHLO_AUTHENTICATION_PROVIDER", "proxy")
    monkeypatch.setenv("PHLO_AUTH_PROXY_SHARED_SECRET", "proxy-secret")
    monkeypatch.setattr("phlo.capabilities.list_capabilities", lambda family: [])

    result = _check_identity_provider()

    assert result.passed is False
    assert "not registered" in result.message


def test_regulated_validation_rejects_unknown_authorization_backend(monkeypatch) -> None:
    from phlo.security.validation import _check_authorization_backend

    monkeypatch.setenv("PHLO_AUTHORIZATION_BACKEND", "foo")
    monkeypatch.setattr("phlo.capabilities.resolve_capability", lambda *_args, **_kwargs: None)

    result = _check_authorization_backend()

    assert result.passed is False
    assert "not registered" in result.message


def test_regulated_validation_requires_registered_authorization_backend(monkeypatch) -> None:
    from phlo.security.validation import _check_authorization_backend

    monkeypatch.setenv("PHLO_AUTHORIZATION_BACKEND", "opa")
    monkeypatch.setattr(
        "phlo.capabilities.resolve_capability",
        lambda *_args, **_kwargs: object(),
    )

    result = _check_authorization_backend()

    assert result.passed is True
    assert "opa" in result.message


def test_regulated_validation_inspects_selected_services(monkeypatch) -> None:
    from phlo.security.validation import _configured_service_names

    monkeypatch.setenv("PHLO_ENABLED_SERVICES", "phlo-api,pgweb")
    monkeypatch.setattr("phlo.infrastructure.config.load_project_config", lambda _root: {})

    assert _configured_service_names() == ["pgweb", "phlo-api"]
