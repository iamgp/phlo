"""Tests for audit correlation ID propagation."""

from __future__ import annotations

from phlo.audit.events import CanonicalAuditEvent


class TestCorrelationFields:
    def test_default_empty_correlation_id(self):
        event = CanonicalAuditEvent(event_type="authorization", surface="test")
        assert event.correlation_id == ""
        assert event.parent_correlation_id == ""

    def test_set_correlation_id(self):
        event = CanonicalAuditEvent(
            event_type="authorization",
            surface="test",
            correlation_id="req-123",
        )
        assert event.correlation_id == "req-123"

    def test_set_parent_correlation_id(self):
        event = CanonicalAuditEvent(
            event_type="authorization",
            surface="test",
            correlation_id="req-456",
            parent_correlation_id="req-123",
        )
        assert event.correlation_id == "req-456"
        assert event.parent_correlation_id == "req-123"

    def test_from_authorization_decision_with_correlation(self):
        event = CanonicalAuditEvent.from_authorization_decision(
            surface="phlo-api",
            actor_subject="alice@example.com",
            actor_type="user",
            actor_roles=("viewer",),
            authentication_source="proxy",
            action="dataset.read",
            resource_type="dataset",
            resource_id="orders",
            decision="allow",
            reason_code="",
            correlation_id="corr-789",
        )
        assert event.correlation_id == "corr-789"

    def test_from_authorization_decision_default_correlation(self):
        event = CanonicalAuditEvent.from_authorization_decision(
            surface="phlo-api",
            actor_subject="alice@example.com",
            actor_type="user",
            actor_roles=(),
            authentication_source="proxy",
            action="dataset.read",
            resource_type="dataset",
            resource_id="orders",
            decision="allow",
            reason_code="",
        )
        assert event.correlation_id == ""


class TestEnforceCorrelation:
    def test_enforce_passes_correlation_to_audit(self, monkeypatch):
        from unittest.mock import MagicMock

        from phlo.capabilities.interfaces import AuthPrincipal, ResourceRef
        from phlo.security.enforcement import EnforcementContext, enforce

        monkeypatch.setattr(EnforcementContext, "_instance", None)

        mock_backend = MagicMock()
        mock_backend.explain_decision.return_value = MagicMock(
            allowed=True, reason_code=None, policy_id=None, explanation=None
        )

        mock_emitter = MagicMock()

        ctx = EnforcementContext.get_instance()
        ctx._authorization_backend = mock_backend
        ctx._audit_emitter = mock_emitter
        ctx._initialized = True

        principal = AuthPrincipal(
            subject="alice@example.com",
            principal_type="user",
            groups=(),
            attributes={"authentication_source": "proxy"},
        )

        enforce(
            principal=principal,
            action="dataset.read",
            resource=ResourceRef(resource_type="dataset", resource_id="orders"),
            surface="phlo-api",
            correlation_id="corr-abc-123",
        )

        call_kwargs = mock_emitter.emit_authorization.call_args.kwargs
        assert call_kwargs["correlation_id"] == "corr-abc-123"

        EnforcementContext.reset_instance()

    def test_enforce_without_correlation_passes_none(self, monkeypatch):
        from unittest.mock import MagicMock

        from phlo.capabilities.interfaces import AuthPrincipal, ResourceRef
        from phlo.security.enforcement import EnforcementContext, enforce

        monkeypatch.setattr(EnforcementContext, "_instance", None)

        mock_backend = MagicMock()
        mock_backend.explain_decision.return_value = MagicMock(
            allowed=True, reason_code=None, policy_id=None, explanation=None
        )

        mock_emitter = MagicMock()

        ctx = EnforcementContext.get_instance()
        ctx._authorization_backend = mock_backend
        ctx._audit_emitter = mock_emitter
        ctx._initialized = True

        principal = AuthPrincipal(
            subject="alice@example.com",
            principal_type="user",
            groups=(),
            attributes={"authentication_source": "proxy"},
        )

        enforce(
            principal=principal,
            action="dataset.read",
            resource=ResourceRef(resource_type="dataset", resource_id="orders"),
            surface="phlo-api",
        )

        call_kwargs = mock_emitter.emit_authorization.call_args.kwargs
        assert call_kwargs["correlation_id"] is None

        EnforcementContext.reset_instance()
