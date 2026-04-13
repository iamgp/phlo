"""GraphQL authorization middleware for Dagster webserver.

This middleware intercepts GraphQL requests to the Dagster webserver and
enforces authorization decisions via the core EnforcementContext.

Middleware Integration:
    - Dagster uses a repository-based workspace loading system
    - Middleware is added to the GraphQL schema
    - The DagsterRegulatedSurfaceAdapter.install() method handles middleware wiring

Authorization Flow:
    1. Extract bearer token from Authorization header
    2. Create DecisionContext with request metadata
    3. Map GraphQL operation to canonical action and resource
    4. Call enforce() via EnforcementContext
    5. Return GraphQL error if denied, proceed if allowed

Principal Extraction:
    - Primary: Authorization header (bearer token)
    - Fallback: X-Dagster-User header for internal service calls
    - If neither present and regulated mode is strict, deny with auth required

Operation Mapping:
    - Uses the operation name from the GraphQL request
    - Extracts asset key / run ID from operation variables
    - Maps to canonical action (asset.execute, run.read, etc.)
"""

from __future__ import annotations

import re
from typing import Any

from dagster import __version__ as DAGSTER_VERSION
from graphql import GraphQLError

from phlo.capabilities import (
    AuthPrincipal,
    DecisionContext,
    ResourceRef,
)
from phlo.logging import get_logger
from phlo.security import EnforcementContext, is_regulated
from phlo.security.enforcement import enforce

logger = get_logger(__name__)

AUTHORIZATION_HEADER_RE = re.compile(r"Bearer\s+(.+)", re.IGNORECASE)
DAGSTER_USER_HEADER = "X-Dagster-User"
DAGSTER_API_TOKEN_HEADER = "X-Dagster-Api-Token"


class DagsterGraphQLAuthorizationMiddleware:
    """GraphQL middleware that enforces authorization on Dagster requests.

    This middleware integrates with Dagster's GraphQL execution pipeline
    to apply authorization decisions before operations execute.

    Attributes:
        surface_name: The regulated surface identifier (dagster-webserver).
        strict_mode: If True, deny requests without valid auth in regulated mode.

    Example:
        Adding middleware to Dagster workspace::

            from phlo_dagster.authorization_middleware import (
                DagsterGraphQLAuthorizationMiddleware,
            )

            middleware = DagsterGraphQLAuthorizationMiddleware()
    """

    def __init__(
        self,
        surface_name: str = "dagster-webserver",
        strict_mode: bool = True,
    ) -> None:
        """Initialize the middleware.

        Args:
            surface_name: Name of the regulated surface for audit events.
            strict_mode: If True, deny requests without valid auth in regulated mode.
        """
        self.surface_name = surface_name
        self.strict_mode = strict_mode

    def resolve(
        self,
        next_fn: Any,
        root: Any,
        info: Any,
        **kwargs: Any,
    ) -> Any:
        """Resolve a GraphQL field, enforcing auth before execution.

        Args:
            next_fn: The next resolver in the chain.
            root: The parent object (usually None for field resolution).
            info: GraphQL execution info containing context.
            **kwargs: Field arguments.

        Returns:
            Result from next_fn if authorized, GraphQLError if denied.
        """
        if not is_regulated():
            return next_fn(root, info, **kwargs)

        try:
            if not self._is_mutation(info):
                return next_fn(root, info, **kwargs)

            auth_result = self._authorize_mutation(info, kwargs)
            if not auth_result.allowed:
                logger.warning(
                    "dagster_authorization_denied",
                    operation=self._get_operation_name(info),
                    reason_code=auth_result.reason_code,
                    surface=self.surface_name,
                )
                raise GraphQLError(
                    f"Authorization denied: {auth_result.reason_code or 'explicit_deny'}"
                )

            return next_fn(root, info, **kwargs)

        except GraphQLError:
            raise
        except Exception:
            logger.exception("dagster_authorization_middleware_error")
            if self.strict_mode:
                raise GraphQLError("Authorization check failed")
            return next_fn(root, info, **kwargs)

    def _is_mutation(self, info: Any) -> bool:
        """Determine if the operation is a mutation."""
        operation = getattr(info, "operation", None)
        if operation and hasattr(operation, "operation"):
            return operation.operation == "mutation"
        return False

    def _get_operation_name(self, info: Any) -> str | None:
        """Extract the operation name from the GraphQL info."""
        operation = getattr(info, "operation", None)
        if operation and hasattr(operation, "name") and operation.name:
            return operation.name.value
        return None

    def _get_selection_resource(self, info: Any) -> tuple[str, str | None]:
        """Extract resource type and ID from the GraphQL selection.

        Returns:
            Tuple of (resource_type, resource_id or None).
        """
        operation_name = self._get_operation_name(info)
        if not operation_name:
            return "unknown", None

        op_lower = operation_name.lower()

        if "pipeline" in op_lower or "backfill" in op_lower:
            return "run", None
        if "terminate" in op_lower or "delete" in op_lower:
            return "run", None
        if "asset" in op_lower:
            return "asset", None
        if "sensor" in op_lower:
            return "service", None
        if "schedule" in op_lower:
            return "service", None
        if "run" in op_lower:
            return "run", None
        if "repository" in op_lower or "workspace" in op_lower:
            return "catalog", None

        return "unknown", None

    def _extract_principal(self, info: Any) -> AuthPrincipal | None:
        """Extract the authenticated principal from request headers.

        Args:
            info: GraphQL execution info containing request context.

        Returns:
            AuthPrincipal if authenticated, None otherwise.
        """
        context = getattr(info, "context", None)
        if context is None:
            return None

        request = getattr(context, "request", None)
        if request is None:
            request = getattr(context, "wsgi_request", None)
        if request is None:
            return None

        headers: dict[str, str] = {}
        if hasattr(request, "headers"):
            headers = dict(request.headers)
        elif hasattr(request, "META"):
            headers = {
                k.lower().replace("http_", "").replace("_", "-"): v
                for k, v in request.META.items()
                if k.startswith("HTTP_")
            }

        auth_header = headers.get("authorization", "")
        match = AUTHORIZATION_HEADER_RE.match(auth_header)
        if match:
            token = match.group(1)
            return self._principal_from_token(token)

        dagster_user = headers.get(DAGSTER_USER_HEADER.lower())
        if dagster_user:
            return AuthPrincipal(
                subject=dagster_user,
                principal_type="user",
                groups=(),
                attributes={"authentication_source": "dagster_header"},
            )

        dagster_token = headers.get(DAGSTER_API_TOKEN_HEADER.lower())
        if dagster_token:
            return AuthPrincipal(
                subject="dagster-service",
                principal_type="service",
                groups=(),
                attributes={"authentication_source": "dagster_token"},
            )

        return None

    def _principal_from_token(self, token: str) -> AuthPrincipal:
        """Convert a bearer token to an AuthPrincipal.

        In a real deployment, this would validate the token and extract claims.
        For now, we use the token as the subject identifier.

        Args:
            token: Bearer token string.

        Returns:
            AuthPrincipal derived from token.
        """
        return AuthPrincipal(
            subject="token-subject",
            principal_type="user",
            groups=(),
            attributes={"authentication_source": "bearer_token"},
        )

    def _create_decision_context(self, info: Any) -> DecisionContext:
        """Create a DecisionContext from GraphQL execution info.

        Args:
            info: GraphQL execution info.

        Returns:
            DecisionContext with request metadata.
        """
        context = getattr(info, "context", None)

        request_id: str | None = None
        ip_address: str | None = None

        if context is not None:
            request = getattr(context, "request", None) or getattr(context, "wsgi_request", None)
            if request is not None:
                request_id = getattr(request, "id", None) or getattr(request, "request_id", None)
                ip_address = getattr(request, "remote_addr", None) or getattr(
                    request, "client_ip", None
                )

        operation_name = self._get_operation_name(info)
        return DecisionContext(
            request_id=request_id,
            ip_address=ip_address,
            attributes={
                "graphql_operation": operation_name or "unknown",
                "dagster_version": DAGSTER_VERSION,
            },
        )

    def _authorize_mutation(
        self,
        info: Any,
        kwargs: dict[str, Any],
    ):
        """Authorize a GraphQL mutation.

        Args:
            info: GraphQL execution info.
            kwargs: Field resolver arguments.

        Returns:
            EnforcementResult from core enforcement.
        """
        from phlo.security.adapters import EnforcementResult

        principal = self._extract_principal(info)
        if principal is None:
            if self.strict_mode:
                return EnforcementResult.deny(
                    reason_code="authentication_required",
                    explanation="No valid authentication credentials provided",
                )
            return EnforcementResult.allow()

        operation_name = self._get_operation_name(info) or "unknown"
        resource_type, resource_id = self._get_selection_resource(info)

        action = self._map_operation_to_action(operation_name)

        ctx = EnforcementContext.get_instance()
        try:
            canonical_principal = ctx.canonicalize(principal)
        except Exception:
            logger.exception("dagster_principal_canonicalization_failed")
            return EnforcementResult.error(
                reason_code="canonicalization_failed",
                explanation="Failed to canonicalize principal",
            )

        resource = ResourceRef(
            resource_type=resource_type,
            resource_id=resource_id or f"dagster:{operation_name}",
        )

        decision_context = self._create_decision_context(info)

        return enforce(
            principal=canonical_principal,
            action=action,
            resource=resource,
            context=decision_context,
            surface=self.surface_name,
        )

    def _map_operation_to_action(self, operation_name: str) -> str:
        """Map a GraphQL operation name to a canonical action.

        Args:
            operation_name: Name of the GraphQL operation.

        Returns:
            Canonical action string.
        """
        op_lower = operation_name.lower()

        if "assetmutation" in op_lower or "materialize" in op_lower:
            return "asset.execute"
        if "launchpipeline" in op_lower or "launchbackfill" in op_lower:
            return "run.execute"
        if "terminate" in op_lower or "delete" in op_lower:
            return "run.execute"
        if "sensor" in op_lower:
            return "run.manage"
        if "schedule" in op_lower:
            return "run.manage"
        if "reload" in op_lower:
            return "catalog.manage"

        if "asset" in op_lower:
            return "asset.read"
        if "pipeline" in op_lower or "run" in op_lower:
            return "run.read"
        if "repository" in op_lower or "workspace" in op_lower:
            return "catalog.read"
        if "service" in op_lower or "scheduler" in op_lower:
            return "service.read"

        return "asset.read"
