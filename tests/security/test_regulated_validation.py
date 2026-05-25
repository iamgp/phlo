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


def test_regulated_validation_accepts_configured_audit_hmac_key(monkeypatch) -> None:
    monkeypatch.setenv("PHLO_REGULATED", "true")
    monkeypatch.setenv("PHLO_AUDIT_HMAC_KEY", "test-audit-key")
    monkeypatch.delenv("PHLO_SIGNATURE_HMAC_KEY", raising=False)

    report = run_regulated_validation(surface_actions=[], surface_resource_types=[])

    check = next(item for item in report.checks if item.name == "compliance_hmac_keys_configured")
    assert check.passed is True
    assert "PHLO_AUDIT_HMAC_KEY is configured" in check.message
