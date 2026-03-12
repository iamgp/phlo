"""Authorization helpers for phlo-api.

This module provides authorization capability integration for FastAPI routes.
"""

from __future__ import annotations

import os
from typing import Any, Callable, TypeVar

from fastapi import HTTPException, Request

from phlo.capabilities import (
    AuthorizationDecision,
    AuthorizationPolicyBackend,
    DecisionContext,
    Principal,
    ResourceRef,
    list_capabilities,
    resolve_capability,
)
from phlo.logging import get_logger

from phlo_api.api.authentication import get_request_principal

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

_ACTION_DATASET_READ = "dataset.read"
_ACTION_DATASET_QUERY = "dataset.query"
_ACTION_ASSET_READ = "asset.read"
_ACTION_ASSET_EXECUTE = "asset.execute"
_ACTION_SERVICE_READ = "service.read"
_ACTION_SERVICE_MANAGE = "service.manage"
_ACTION_ADMIN_READ = "admin.read"
_ACTION_ADMIN_MANAGE = "admin.manage"
_AUTHORIZATION_BACKEND_ENV = "PHLO_AUTHORIZATION_BACKEND"


def get_authorization_backend() -> AuthorizationPolicyBackend | None:
    """Resolve the authorization policy backend capability.

    Returns None if no backend is configured.
    Raises when multiple backends are installed without an explicit selection.
    """
    backend_name = os.environ.get(_AUTHORIZATION_BACKEND_ENV)
    result = resolve_capability("authorization_policy_backend", backend_name)
    if backend_name and result is None:
        raise RuntimeError(
            f"Authorization backend {backend_name!r} is not registered. "
            f"Set {_AUTHORIZATION_BACKEND_ENV} to a valid backend name."
        )

    if result is None:
        available_backends = list_capabilities("authorization_policy_backend")
        if not available_backends:
            logger.debug("no_authorization_backend_configured")
            return None
        if backend_name is None and len(available_backends) > 1:
            raise RuntimeError(
                "Multiple authorization backends are registered. "
                f"Set {_AUTHORIZATION_BACKEND_ENV} to one of: {', '.join(sorted(available_backends))}."
            )
        logger.debug("no_authorization_backend_configured")
        return None
    return result.provider


def require_authorization_backend() -> AuthorizationPolicyBackend:
    """Resolve the authorization policy backend or raise if not available."""
    backend = get_authorization_backend()
    if backend is None:
        raise RuntimeError("Authorization backend not configured")
    return backend


def create_decision_context(
    request: Request,
    environment: str | None = None,
) -> DecisionContext:
    """Create a DecisionContext from a FastAPI request."""
    return DecisionContext(
        environment=environment,
        request_id=request.state.request_id if hasattr(request.state, "request_id") else None,
        ip_address=request.client.host if request.client else None,
        attributes={
            "method": request.method,
            "path": request.url.path,
        },
    )


def resolve_request_principal(request: Request, require_auth: bool = False) -> Principal | None:
    """Resolve the principal from the request using authentication capability.

    Uses the configured authentication provider to get the AuthPrincipal,
    then applies canonical role mapping to produce the authz Principal.

    Args:
        request: The FastAPI request
        require_auth: If True, returns None when authentication fails or is not configured.
                     If False (default), falls back to anonymous principal for backward compat.

    Returns:
        Principal if authenticated (or require_auth=False), None if require_auth=True and not authenticated.
    """
    auth_principal = get_request_principal(request)
    if auth_principal is None:
        if require_auth:
            return None
        return _default_principal()

    return _authn_to_authz_principal(auth_principal)


def _authn_to_authz_principal(auth_principal: Any) -> Principal:
    """Convert AuthPrincipal from authentication to authz Principal.

    Applies canonical role mapping based on authentication attributes.
    Only maps known group names to canonical roles; unknown groups are discarded.
    """
    roles = _map_groups_to_roles(auth_principal.groups)
    roles = _apply_principal_type_roles(auth_principal.principal_type, roles)

    return Principal(
        subject=auth_principal.subject,
        principal_type=auth_principal.principal_type,
        roles=roles,
        attributes=dict(auth_principal.attributes),
    )


def _map_groups_to_roles(groups: tuple[str, ...]) -> tuple[str, ...]:
    """Map authentication groups to canonical roles.

    Only known group names are mapped to canonical roles.
    Unknown groups are discarded to prevent privilege escalation
    based on IdP-native group names.
    """
    role_mapping = {
        "admin": "admin",
        "operators": "operator",
        "developers": "developer",
        "analysts": "analyst",
        "viewers": "viewer",
    }
    roles = []
    for group in groups:
        if group in role_mapping and role_mapping[group] not in roles:
            roles.append(role_mapping[group])
    return tuple(roles)


def _apply_principal_type_roles(
    principal_type: str, existing_roles: tuple[str, ...]
) -> tuple[str, ...]:
    """Apply default roles based on principal type."""
    if principal_type == "service":
        if "service" not in existing_roles:
            return (*existing_roles, "service") if existing_roles else ("service",)
    return existing_roles


def _default_principal() -> Principal:
    """Return the default anonymous principal.

    Returns a principal with no roles to ensure fail-closed behavior.
    Unauthenticated requests will be denied by the PDP's default-deny policy.
    """
    return Principal(
        subject="anonymous",
        principal_type="user",
        roles=(),
    )


def check_dataset_read(
    request: Request,
    dataset_id: str,
    environment: str | None = None,
    require_auth: bool = True,
) -> None:
    """Check if the request can read the dataset."""
    backend = get_authorization_backend()
    if backend is None:
        return

    principal = resolve_request_principal(request, require_auth=require_auth)
    if principal is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "reason": "authentication_required"},
        )
    resource = ResourceRef(
        resource_type="dataset",
        resource_id=dataset_id,
    )
    context = create_decision_context(request, environment)

    if not backend.is_allowed(principal, _ACTION_DATASET_READ, resource, context):
        decision = backend.explain_decision(principal, _ACTION_DATASET_READ, resource, context)
        _log_deny(principal, _ACTION_DATASET_READ, resource, decision)
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "reason": decision.reason_code},
        )


def check_dataset_query(
    request: Request,
    dataset_id: str,
    environment: str | None = None,
    require_auth: bool = True,
) -> None:
    """Check if the request can query the dataset."""
    backend = get_authorization_backend()
    if backend is None:
        return

    principal = resolve_request_principal(request, require_auth=require_auth)
    if principal is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "reason": "authentication_required"},
        )
    resource = ResourceRef(
        resource_type="dataset",
        resource_id=dataset_id,
    )
    context = create_decision_context(request, environment)

    if not backend.is_allowed(principal, _ACTION_DATASET_QUERY, resource, context):
        decision = backend.explain_decision(principal, _ACTION_DATASET_QUERY, resource, context)
        _log_deny(principal, _ACTION_DATASET_QUERY, resource, decision)
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "reason": decision.reason_code},
        )


def check_asset_read(
    request: Request,
    asset_id: str,
    environment: str | None = None,
    require_auth: bool = True,
) -> None:
    """Check if the request can read the asset."""
    backend = get_authorization_backend()
    if backend is None:
        return

    principal = resolve_request_principal(request, require_auth=require_auth)
    if principal is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "reason": "authentication_required"},
        )
    resource = ResourceRef(
        resource_type="asset",
        resource_id=asset_id,
    )
    context = create_decision_context(request, environment)

    if not backend.is_allowed(principal, _ACTION_ASSET_READ, resource, context):
        decision = backend.explain_decision(principal, _ACTION_ASSET_READ, resource, context)
        _log_deny(principal, _ACTION_ASSET_READ, resource, decision)
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "reason": decision.reason_code},
        )


def check_asset_execute(
    request: Request,
    asset_id: str,
    environment: str | None = None,
    require_auth: bool = True,
) -> None:
    """Check if the request can execute the asset."""
    backend = get_authorization_backend()
    if backend is None:
        return

    principal = resolve_request_principal(request, require_auth=require_auth)
    if principal is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "reason": "authentication_required"},
        )
    resource = ResourceRef(
        resource_type="asset",
        resource_id=asset_id,
    )
    context = create_decision_context(request, environment)

    if not backend.is_allowed(principal, _ACTION_ASSET_EXECUTE, resource, context):
        decision = backend.explain_decision(principal, _ACTION_ASSET_EXECUTE, resource, context)
        _log_deny(principal, _ACTION_ASSET_EXECUTE, resource, decision)
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "reason": decision.reason_code},
        )


def check_service_read(
    request: Request,
    service_id: str,
    environment: str | None = None,
    require_auth: bool = True,
) -> None:
    """Check if the request can read the service."""
    backend = get_authorization_backend()
    if backend is None:
        return

    principal = resolve_request_principal(request, require_auth=require_auth)
    if principal is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "reason": "authentication_required"},
        )
    resource = ResourceRef(
        resource_type="service",
        resource_id=service_id,
    )
    context = create_decision_context(request, environment)

    if not backend.is_allowed(principal, _ACTION_SERVICE_READ, resource, context):
        decision = backend.explain_decision(principal, _ACTION_SERVICE_READ, resource, context)
        _log_deny(principal, _ACTION_SERVICE_READ, resource, decision)
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "reason": decision.reason_code},
        )


def check_service_manage(
    request: Request,
    service_id: str,
    environment: str | None = None,
    require_auth: bool = True,
) -> None:
    """Check if the request can manage the service."""
    backend = get_authorization_backend()
    if backend is None:
        return

    principal = resolve_request_principal(request, require_auth=require_auth)
    if principal is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "reason": "authentication_required"},
        )
    resource = ResourceRef(
        resource_type="service",
        resource_id=service_id,
    )
    context = create_decision_context(request, environment)

    if not backend.is_allowed(principal, _ACTION_SERVICE_MANAGE, resource, context):
        decision = backend.explain_decision(principal, _ACTION_SERVICE_MANAGE, resource, context)
        _log_deny(principal, _ACTION_SERVICE_MANAGE, resource, decision)
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "reason": decision.reason_code},
        )


def check_admin_read(
    request: Request,
    admin_id: str,
    environment: str | None = None,
    require_auth: bool = True,
) -> None:
    """Check if the request can read admin resources."""
    backend = get_authorization_backend()
    if backend is None:
        return

    principal = resolve_request_principal(request, require_auth=require_auth)
    if principal is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "reason": "authentication_required"},
        )
    resource = ResourceRef(
        resource_type="admin",
        resource_id=admin_id,
    )
    context = create_decision_context(request, environment)

    if not backend.is_allowed(principal, _ACTION_ADMIN_READ, resource, context):
        decision = backend.explain_decision(principal, _ACTION_ADMIN_READ, resource, context)
        _log_deny(principal, _ACTION_ADMIN_READ, resource, decision)
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "reason": decision.reason_code},
        )


def check_admin_manage(
    request: Request,
    admin_id: str,
    environment: str | None = None,
    require_auth: bool = True,
) -> None:
    """Check if the request can manage admin resources."""
    backend = get_authorization_backend()
    if backend is None:
        return

    principal = resolve_request_principal(request, require_auth=require_auth)
    if principal is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "reason": "authentication_required"},
        )
    resource = ResourceRef(
        resource_type="admin",
        resource_id=admin_id,
    )
    context = create_decision_context(request, environment)

    if not backend.is_allowed(principal, _ACTION_ADMIN_MANAGE, resource, context):
        decision = backend.explain_decision(principal, _ACTION_ADMIN_MANAGE, resource, context)
        _log_deny(principal, _ACTION_ADMIN_MANAGE, resource, decision)
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "reason": decision.reason_code},
        )


def filter_datasets(
    request: Request,
    dataset_ids: list[str],
    action: str = _ACTION_DATASET_READ,
    environment: str | None = None,
    require_auth: bool = True,
) -> list[str]:
    """Filter a list of dataset IDs to only those the principal can access."""
    backend = get_authorization_backend()
    if backend is None:
        return dataset_ids

    principal = resolve_request_principal(request, require_auth=require_auth)
    if principal is None:
        return []
    resources = [ResourceRef(resource_type="dataset", resource_id=d_id) for d_id in dataset_ids]
    context = create_decision_context(request, environment)

    allowed_resources = backend.filter_resources(principal, resources, action, context)
    return [r.resource_id for r in allowed_resources]


def _log_deny(
    principal: Principal,
    action: str,
    resource: ResourceRef,
    decision: AuthorizationDecision,
) -> None:
    """Log authorization denial for auditing."""
    logger.warning(
        "authorization_denied",
        principal=principal.subject,
        principal_type=principal.principal_type,
        roles=list(principal.roles),
        action=action,
        resource_type=resource.resource_type,
        resource_id=resource.resource_id,
        reason_code=decision.reason_code,
        policy_id=decision.policy_id,
    )
