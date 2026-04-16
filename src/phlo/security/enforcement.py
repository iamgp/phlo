"""Core enforcement engine for regulated access.

This module provides the core enforcement path owned by phlo.security.
It is invoked by surface adapters to make authorization decisions.

The EnforcementContext is a process-scoped lazy singleton that owns:
- Identity bridge (for principal canonicalization)
- Authorization policy backend (for PDP decisions)
- Audit event emitter (for canonical audit events)

Core enforcement must NOT import FastAPI, Click, or Dagster/Starlette types.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from phlo.logging import get_logger
from phlo.security.adapters import EnforcementResult

if TYPE_CHECKING:
    from phlo.capabilities.interfaces import (
        AuthorizationDecision,
        AuthorizationPolicyBackend,
        DecisionContext,
        Principal,
        ResourceRef,
    )
    from phlo.identity.bridge import IdentityBridge

logger = get_logger(__name__)


class EnforcementContext:
    """Process-scoped lazy singleton for core enforcement.

    Holds the shared infrastructure for all regulated surface enforcement:
    identity bridge, authorization policy backend, and audit emitter.
    Adapters do not hold their own cached instances of these — they use
    EnforcementContext.get_instance() which owns the singleton.

    Thread-safe lazy initialization using double-checked locking.
    """

    _instance: EnforcementContext | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._identity_bridge: IdentityBridge | None = None
        self._authorization_backend: AuthorizationPolicyBackend | None = None
        self._audit_emitter: Any = None
        self._initialized = False
        self._init_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> EnforcementContext:
        """Return the process-scoped EnforcementContext singleton."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance. For testing only."""
        with cls._lock:
            cls._instance = None

    @property
    def identity_bridge(self) -> IdentityBridge:
        """Lazy-initialized identity bridge."""
        if self._identity_bridge is None:
            with self._init_lock:
                if self._identity_bridge is None:
                    from phlo.identity.bridge import create_regulated_bridge

                    self._identity_bridge = create_regulated_bridge()
        return self._identity_bridge

    @property
    def authorization_backend(self) -> AuthorizationPolicyBackend:
        """Lazy-initialized authorization policy backend."""
        if self._authorization_backend is None:
            with self._init_lock:
                if self._authorization_backend is None:
                    from phlo.capabilities import resolve_capability

                    result = resolve_capability("authorization_policy_backend")
                    if result is None:
                        msg = "No authorization_policy_backend registered"
                        raise RuntimeError(msg)
                    self._authorization_backend = result.provider
        return self._authorization_backend

    @property
    def audit_emitter(self) -> Any:
        """Lazy-initialized audit event emitter."""
        if self._audit_emitter is None:
            with self._init_lock:
                if self._audit_emitter is None:
                    from phlo.audit.events import create_default_emitter

                    self._audit_emitter = create_default_emitter(surface="core")
        return self._audit_emitter

    def canonicalize(self, auth_principal: Any) -> Principal:
        """Canonicalize an AuthPrincipal to a Principal via the identity bridge."""
        return self.identity_bridge.canonicalize(auth_principal)


def enforce(
    principal: Any,
    action: str,
    resource: ResourceRef,
    context: DecisionContext | None = None,
    request_id: str | None = None,
    surface: str = "unknown",
    correlation_id: str | None = None,
) -> EnforcementResult:
    """Make an authorization decision and emit a canonical audit event.

    This is the core enforcement function called by surface adapters.
    It canonicalizes the principal, resolves the PDP, and emits an audit event.

    Args:
        principal: AuthPrincipal or Principal from the surface adapter.
        action: Canonical action name (e.g., "dataset.read").
        resource: ResourceRef for the resource being accessed.
        context: Optional decision context.
        request_id: Optional request correlation ID for audit.
        surface: Name of the surface invoking enforcement (e.g., "phlo-api").
        correlation_id: Optional end-to-end correlation ID across services.

    Returns:
        EnforcementResult: allow, deny, or error.
    """
    ctx = EnforcementContext.get_instance()

    try:
        canonical_principal = ctx.canonicalize(principal)
    except Exception:
        logger.exception("identity_canonicalization_failed")
        return EnforcementResult.error(
            reason_code="canonicalization_failed",
            explanation="Failed to canonicalize principal",
        )

    try:
        decision: AuthorizationDecision = ctx.authorization_backend.explain_decision(
            canonical_principal, action, resource, context
        )
    except Exception:
        logger.exception("authorization_backend_failed")
        return EnforcementResult.error(
            reason_code="backend_unavailable",
            explanation="Authorization backend failed",
        )

    if decision.allowed:
        result = EnforcementResult.allow()
    else:
        result = EnforcementResult.deny(
            reason_code=decision.reason_code or "explicit_deny",
            policy_id=decision.policy_id,
            explanation=decision.explanation,
        )

    try:
        ctx.audit_emitter.emit_authorization(
            surface=surface,
            action=action,
            resource_type=resource.resource_type,
            resource_id=resource.resource_id,
            actor_subject=canonical_principal.subject,
            actor_type=canonical_principal.principal_type,
            actor_roles=canonical_principal.roles,
            authentication_source=canonical_principal.attributes.get(
                "authentication_source", "unknown"
            ),
            decision=result.variant,
            reason_code=result.reason_code or "",
            policy_id=result.policy_id,
            request_id=request_id,
            correlation_id=correlation_id,
        )
    except Exception:
        logger.exception("audit_emission_failed")

    return result
