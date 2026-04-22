"""Canonical audit event library.

This module provides the shared canonical audit event schema and infrastructure
for regulated mode. All approved surfaces must emit audit events using this
contract for authorization decisions, authentication events, and privileged
mutations.

Audit Event Contract v1:
    All audit events must include the top-level fields defined in CanonicalAuditEvent.
    The envelope is consistent across authn, authz, and mutation events.

Regulated Mode Requirements:
    - One shared library owns this contract
    - Authn and authz events use the same envelope
    - Explanatory decision data comes from AuthorizationDecision
    - Privileged mutation allows must emit allow events
    - Denied actions must emit deny events
    - Settings/history records must also emit canonical audit events
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from phlo.logging import get_logger

logger = get_logger(__name__)

# Schema version for the canonical audit event contract
AUDIT_SCHEMA_VERSION = "1.0"


class AuditEventType(StrEnum):
    """Types of audit events."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    MUTATION = "mutation"
    ADMIN = "admin"
    SYSTEM = "system"


class AuditDecision(StrEnum):
    """Decision outcomes for audit events."""

    ALLOW = "allow"
    DENY = "deny"
    ERROR = "error"
    SKIP = "skip"


class AuditOutcome(StrEnum):
    """Execution outcomes for audit events."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


@dataclass(frozen=True)
class CanonicalAuditEvent:
    """Canonical audit event v1.

    This is the normative contract for audit events in regulated mode.
    All approved surfaces must emit events using this schema.

    Required Fields:
        schema_version: Audit schema version (always "1.0").
        event_type: Type of audit event (authentication, authorization, etc.).
        event_id: Unique identifier for this event (UUID).
        timestamp: ISO 8601 timestamp of the event.
        surface: Surface that generated the event (e.g., "phlo-api", "dagster").

    Actor Fields:
        actor_subject: Subject identifier of the actor.
        actor_type: Type of actor (user, service, platform).
        actor_roles: Roles assigned to the actor at decision time.
        authentication_source: Source of authentication (IdP, proxy, etc.).

    Action Fields:
        action: Canonical action being attempted.
        resource_type: Canonical resource type being accessed.
        resource_id: Stable resource identifier.

    Decision Fields:
        decision: Allow, deny, error, or skip.
        reason_code: Machine-readable reason for the decision.
        policy_id: ID of the policy that produced the decision (if applicable).

    Context Fields:
        request_id: Request or correlation ID.
        run_id: Run ID for pipeline executions.
        source_ip: Source IP address when available.
        correlation_id: End-to-end correlation across services.
        parent_correlation_id: Correlation ID of the parent/initiating request.

    Mutation Fields (when applicable):
        target_state_before: State before mutation.
        target_state_after: State after mutation.
        change_reason: Reason for the change.

    Outcome:
        outcome: Success, failure, or partial.
    """

    # Required fields
    schema_version: str = AUDIT_SCHEMA_VERSION
    event_type: str = ""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    surface: str = ""

    # Actor fields
    actor_subject: str = ""
    actor_type: str = ""
    actor_roles: tuple[str, ...] = ()
    authentication_source: str = ""

    # Action fields
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""

    # Decision fields
    decision: str = ""
    reason_code: str = ""
    policy_id: str | None = None
    explanation: str | None = None

    # Context fields
    request_id: str | None = None
    run_id: str | None = None
    source_ip: str | None = None
    correlation_id: str = ""
    parent_correlation_id: str = ""

    # Mutation fields
    target_state_before: dict[str, Any] | None = None
    target_state_after: dict[str, Any] | None = None
    change_reason: str | None = None

    # Outcome
    outcome: str = ""

    # Additional attributes for extensibility
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the audit event to a dictionary.

        Returns:
            Dictionary representation of the audit event.
        """
        result = asdict(self)
        # Convert tuples to lists for JSON serialization
        result["actor_roles"] = list(self.actor_roles)
        return result

    @classmethod
    def from_authorization_decision(
        cls,
        *,
        surface: str,
        actor_subject: str,
        actor_type: str,
        actor_roles: tuple[str, ...],
        authentication_source: str,
        action: str,
        resource_type: str,
        resource_id: str,
        decision: str,
        reason_code: str,
        policy_id: str | None = None,
        explanation: str | None = None,
        request_id: str | None = None,
        source_ip: str | None = None,
        outcome: str = "",
        correlation_id: str = "",
    ) -> CanonicalAuditEvent:
        """Create an audit event from an authorization decision.

        Args:
            surface: Surface that generated the event.
            actor_subject: Subject identifier.
            actor_type: Type of actor.
            actor_roles: Roles assigned to actor.
            authentication_source: Source of authentication.
            action: Canonical action.
            resource_type: Canonical resource type.
            resource_id: Resource identifier.
            decision: Decision outcome (allow, deny, error, skip).
            reason_code: Machine-readable reason.
            policy_id: Policy ID if applicable.
            explanation: Human-readable explanation.
            request_id: Request correlation ID.
            source_ip: Source IP address.
            outcome: Execution outcome.
            correlation_id: End-to-end correlation across services.

        Returns:
            CanonicalAuditEvent populated from the decision.
        """
        return cls(
            event_type=AuditEventType.AUTHORIZATION,
            surface=surface,
            actor_subject=actor_subject,
            actor_type=actor_type,
            actor_roles=actor_roles,
            authentication_source=authentication_source,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            decision=decision,
            reason_code=reason_code,
            policy_id=policy_id,
            explanation=explanation,
            request_id=request_id,
            source_ip=source_ip,
            outcome=outcome,
            correlation_id=correlation_id,
        )


class AuditEventEmitter:
    """Emitter for canonical audit events.

    This class provides the interface for emitting audit events in regulated mode.
    All approved surfaces use this emitter to ensure consistent audit trails.

    The emitter supports multiple sinks and can be configured for different
    retention and routing policies.

    Example:
        >>> from phlo.audit.events import AuditEventEmitter, CanonicalAuditEvent
        >>> emitter = AuditEventEmitter()
        >>> event = CanonicalAuditEvent(...)
        >>> emitter.emit(event)
    """

    def __init__(self, surface: str) -> None:
        """Initialize the audit event emitter.

        Args:
            surface: Name of the surface emitting events (e.g., "phlo-api").
        """
        self.surface = surface
        self._sinks: list[AuditEventSink] = []

    def add_sink(self, sink: AuditEventSink) -> None:
        """Add an audit event sink.

        Args:
            sink: Sink to add for event delivery.
        """
        self._sinks.append(sink)

    def emit(self, event: CanonicalAuditEvent) -> None:
        """Emit an audit event to all configured sinks.

        Args:
            event: The audit event to emit.
        """
        # Create a new event with the correct surface if not set
        if not event.surface:
            from dataclasses import replace

            event = replace(event, surface=self.surface)

        logger.debug(
            "audit_event_emitted",
            event_id=event.event_id,
            event_type=event.event_type,
            surface=event.surface,
            actor=event.actor_subject,
            action=event.action,
            decision=event.decision,
        )

        for sink in self._sinks:
            try:
                sink.write(event)
            except Exception as e:
                logger.error(
                    "audit_sink_write_failed",
                    sink_type=type(sink).__name__,
                    event_id=event.event_id,
                    error=str(e),
                )

    def emit_authorization(
        self,
        *,
        actor_subject: str,
        actor_type: str,
        actor_roles: tuple[str, ...],
        authentication_source: str,
        action: str,
        resource_type: str,
        resource_id: str,
        decision: str,
        reason_code: str,
        policy_id: str | None = None,
        explanation: str | None = None,
        request_id: str | None = None,
        source_ip: str | None = None,
        outcome: str = "",
        correlation_id: str | None = None,
    ) -> None:
        """Emit an authorization audit event.

        Convenience method for emitting authorization events.

        Args:
            actor_subject: Subject identifier.
            actor_type: Type of actor.
            actor_roles: Roles assigned to actor.
            authentication_source: Source of authentication.
            action: Canonical action.
            resource_type: Canonical resource type.
            resource_id: Resource identifier.
            decision: Decision outcome.
            reason_code: Machine-readable reason.
            policy_id: Policy ID if applicable.
            explanation: Human-readable explanation.
            request_id: Request correlation ID.
            source_ip: Source IP address.
            outcome: Execution outcome.
            correlation_id: End-to-end correlation across services.
        """
        event = CanonicalAuditEvent.from_authorization_decision(
            surface=self.surface,
            actor_subject=actor_subject,
            actor_type=actor_type,
            actor_roles=actor_roles,
            authentication_source=authentication_source,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            decision=decision,
            reason_code=reason_code,
            policy_id=policy_id,
            explanation=explanation,
            request_id=request_id,
            source_ip=source_ip,
            outcome=outcome,
            correlation_id=correlation_id or "",
        )
        self.emit(event)

    def emit_mutation(
        self,
        *,
        actor_subject: str,
        actor_type: str,
        actor_roles: tuple[str, ...],
        authentication_source: str,
        action: str,
        resource_type: str,
        resource_id: str,
        target_state_before: dict[str, Any] | None = None,
        target_state_after: dict[str, Any] | None = None,
        change_reason: str | None = None,
        request_id: str | None = None,
        source_ip: str | None = None,
        outcome: str = "",
    ) -> None:
        """Emit a mutation audit event.

        Convenience method for emitting mutation events.

        Args:
            actor_subject: Subject identifier.
            actor_type: Type of actor.
            actor_roles: Roles assigned to actor.
            authentication_source: Source of authentication.
            action: Canonical action.
            resource_type: Canonical resource type.
            resource_id: Resource identifier.
            target_state_before: State before mutation.
            target_state_after: State after mutation.
            change_reason: Reason for the change.
            request_id: Request correlation ID.
            source_ip: Source IP address.
            outcome: Execution outcome.
        """
        event = CanonicalAuditEvent(
            event_type=AuditEventType.MUTATION,
            surface=self.surface,
            actor_subject=actor_subject,
            actor_type=actor_type,
            actor_roles=actor_roles,
            authentication_source=authentication_source,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            decision=AuditDecision.ALLOW,  # Mutations are only audited when allowed
            reason_code="mutation_executed",
            target_state_before=target_state_before,
            target_state_after=target_state_after,
            change_reason=change_reason,
            request_id=request_id,
            source_ip=source_ip,
            outcome=outcome,
        )
        self.emit(event)


class AuditEventSink:
    """Base class for audit event sinks.

    Implementations must provide the write() method.
    """

    def write(self, event: CanonicalAuditEvent) -> None:
        """Write an audit event to the sink.

        Args:
            event: The audit event to write.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError


class LoggingAuditSink(AuditEventSink):
    """Audit sink that writes to structured logs.

    This is the default sink for audit events. Events are written
    as structured log entries at INFO level.
    """

    def __init__(self, logger_name: str = "phlo.audit") -> None:
        """Initialize the logging sink.

        Args:
            logger_name: Name of the logger to use.
        """
        self._logger = get_logger(logger_name)

    def write(self, event: CanonicalAuditEvent) -> None:
        """Write an audit event to the log.

        Args:
            event: The audit event to write.
        """
        self._logger.info(
            "canonical_audit_event",
            **event.to_dict(),
        )


def create_default_emitter(surface: str) -> AuditEventEmitter:
    """Create an audit event emitter with default configuration.

    The default configuration includes a logging sink for audit events.

    Args:
        surface: Name of the surface emitting events.

    Returns:
        AuditEventEmitter with default sinks configured.
    """
    emitter = AuditEventEmitter(surface)
    emitter.add_sink(LoggingAuditSink())
    return emitter
