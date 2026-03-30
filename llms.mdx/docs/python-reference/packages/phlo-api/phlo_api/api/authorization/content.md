# authorization (/docs/python-reference/packages/phlo-api/phlo_api/api/authorization)



Authorization helpers for phlo-api.

This module provides authorization capability integration for FastAPI routes.
It implements role-based access control (RBAC) with canonical role mapping
from authentication groups.

Key Functions:
get\_authorization\_backend: Resolve the configured authorization backend.
check\_dataset\_read: Verify read permission on a dataset.
check\_dataset\_query: Verify query permission on a dataset.
check\_asset\_read: Verify read permission on an asset.
filter\_datasets: Filter datasets by access permission.

Environment Variables:
PHLO\_AUTHORIZATION\_BACKEND: Name of the authorization backend to use.
Required when multiple backends are installed.

Example:
Enforcing authorization in a FastAPI route:

.. code-block:: python

from fastapi import Request
from phlo\_api.api.authorization import check\_dataset\_read

@app.get("/datasets/\{dataset\_id}")
async def get\_dataset(dataset\_id: str, request: Request):
check\_dataset\_read(request, dataset\_id)
return \{"dataset": dataset\_id}

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;F&#x22;" type="null" value="&#x22;TypeVar('F', bound=(Callable[..., Any]))&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_authorization_backend&#x22;" type="&#x22;() -> AuthorizationPolicyBackend | None&#x22;">
      Resolve the authorization policy backend capability.

      Returns None if no backend is configured. Raises when multiple backends
      are installed without an explicit selection.

      <PySourceCode>
        ```python
        def get_authorization_backend() -> AuthorizationPolicyBackend | None:
            """Resolve the authorization policy backend capability.

            Returns None if no backend is configured. Raises when multiple backends
            are installed without an explicit selection.

            Args:
                None: No arguments required.

            Returns:
                AuthorizationPolicyBackend instance, or None if not configured.

            Raises:
                RuntimeError: If the configured backend is not registered, or if multiple
                    backends are available without explicit selection.

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
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;AuthorizationPolicyBackend | None&#x22;">
        AuthorizationPolicyBackend instance, or None if not configured.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;require_authorization_backend&#x22;" type="&#x22;() -> AuthorizationPolicyBackend&#x22;">
      Resolve the authorization policy backend or raise if not available.

      <PySourceCode>
        ```python
        def require_authorization_backend() -> AuthorizationPolicyBackend:
            """Resolve the authorization policy backend or raise if not available.

            Args:
                None: No arguments required.

            Returns:
                AuthorizationPolicyBackend instance.

            Raises:
                RuntimeError: If no authorization backend is configured.

            """
            backend = get_authorization_backend()
            if backend is None:
                raise RuntimeError("Authorization backend not configured")
            return backend
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.capabilities.AuthorizationPolicyBackend&#x22;">
        AuthorizationPolicyBackend instance.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;create_decision_context&#x22;" type="&#x22;(request, environment=None) -> DecisionContext&#x22;">
      Create a DecisionContext from a FastAPI request.

      <PySourceCode>
        ```python
        def create_decision_context(
            request: Request,
            environment: str | None = None,
        ) -> DecisionContext:
            """Create a DecisionContext from a FastAPI request.

            Args:
                request: The FastAPI request object.
                environment: Optional environment identifier.

            Returns:
                DecisionContext populated with request metadata.

            Raises:
                None: No exceptions raised directly.

            """
            return DecisionContext(
                environment=environment,
                request_id=request.state.request_id if hasattr(request.state, "request_id") else None,
                ip_address=request.client.host if request.client else None,
                attributes={
                    "method": request.method,
                    "path": request.url.path,
                },
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="undefined">
          The FastAPI request object.
        </PyParameter>

        <PyParameter name="&#x22;environment&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional environment identifier.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo.capabilities.DecisionContext&#x22;">
        DecisionContext populated with request metadata.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;resolve_request_principal&#x22;" type="&#x22;(request, require_auth=False) -> Principal | None&#x22;">
      Resolve the principal from the request using authentication capability.

      Uses the configured authentication provider to get the AuthPrincipal,
      then applies canonical role mapping to produce the authz Principal.

      <PySourceCode>
        ```python
        def resolve_request_principal(request: Request, require_auth: bool = False) -> Principal | None:
            """Resolve the principal from the request using authentication capability.

            Uses the configured authentication provider to get the AuthPrincipal,
            then applies canonical role mapping to produce the authz Principal.

            Args:
                request: The FastAPI request object.
                require_auth: If True, returns None when authentication fails or is not configured.
                    If False (default), falls back to anonymous principal for backward compat.

            Returns:
                Principal if authenticated (or require_auth=False), None if require_auth=True
                    and not authenticated.

            Raises:
                None: No exceptions raised directly.

            """
            auth_principal = get_request_principal(request)
            if auth_principal is None:
                if require_auth:
                    return None
                return _default_principal()

            return _authn_to_authz_principal(auth_principal)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="undefined">
          The FastAPI request object.
        </PyParameter>

        <PyParameter name="&#x22;require_auth&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
          If True, returns None when authentication fails or is not configured.
          If False (default), falls back to anonymous principal for backward compat.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;Principal | None&#x22;">
        Principal if authenticated (or require\_auth=False), None if require\_auth=True
        and not authenticated.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_authn_to_authz_principal&#x22;" type="&#x22;(auth_principal) -> Principal&#x22;">
      Convert AuthPrincipal from authentication to authz Principal.

      Applies canonical role mapping based on authentication attributes.
      Only maps known group names to canonical roles; unknown groups are discarded.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;auth_principal&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.capabilities.Principal&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_map_groups_to_roles&#x22;" type="&#x22;(groups) -> tuple[str, ...]&#x22;">
      Map authentication groups to canonical roles.

      Only known group names are mapped to canonical roles.
      Unknown groups are discarded to prevent privilege escalation
      based on IdP-native group names.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;groups&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;tuple[str, ...]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_apply_principal_type_roles&#x22;" type="&#x22;(principal_type, existing_roles) -> tuple[str, ...]&#x22;">
      Apply default roles based on principal type.

      <PySourceCode>
        ```python
        def _apply_principal_type_roles(
            principal_type: str, existing_roles: tuple[str, ...]
        ) -> tuple[str, ...]:
            """Apply default roles based on principal type."""
            if principal_type == "service":
                if "service" not in existing_roles:
                    return (*existing_roles, "service") if existing_roles else ("service",)
            return existing_roles
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;principal_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;existing_roles&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;tuple[str, ...]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_default_principal&#x22;" type="&#x22;() -> Principal&#x22;">
      Return the default anonymous principal.

      Returns a principal with no roles to ensure fail-closed behavior.
      Unauthenticated requests will be denied by the PDP's default-deny policy.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.capabilities.Principal&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;check_dataset_read&#x22;" type="&#x22;(request, dataset_id, environment=None, require_auth=True) -> None&#x22;">
      Check if the request can read the dataset.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="null" />

        <PyParameter name="&#x22;dataset_id&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;environment&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;require_auth&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;check_dataset_query&#x22;" type="&#x22;(request, dataset_id, environment=None, require_auth=True) -> None&#x22;">
      Check if the request can query the dataset.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="null" />

        <PyParameter name="&#x22;dataset_id&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;environment&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;require_auth&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;check_asset_read&#x22;" type="&#x22;(request, asset_id, environment=None, require_auth=True) -> None&#x22;">
      Check if the request can read the asset.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="null" />

        <PyParameter name="&#x22;asset_id&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;environment&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;require_auth&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;check_asset_execute&#x22;" type="&#x22;(request, asset_id, environment=None, require_auth=True) -> None&#x22;">
      Check if the request can execute the asset.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="null" />

        <PyParameter name="&#x22;asset_id&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;environment&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;require_auth&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;check_service_read&#x22;" type="&#x22;(request, service_id, environment=None, require_auth=True) -> None&#x22;">
      Check if the request can read the service.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="null" />

        <PyParameter name="&#x22;service_id&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;environment&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;require_auth&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;check_service_manage&#x22;" type="&#x22;(request, service_id, environment=None, require_auth=True) -> None&#x22;">
      Check if the request can manage the service.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="null" />

        <PyParameter name="&#x22;service_id&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;environment&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;require_auth&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;check_admin_read&#x22;" type="&#x22;(request, admin_id, environment=None, require_auth=True) -> None&#x22;">
      Check if the request can read admin resources.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="null" />

        <PyParameter name="&#x22;admin_id&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;environment&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;require_auth&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;check_admin_manage&#x22;" type="&#x22;(request, admin_id, environment=None, require_auth=True) -> None&#x22;">
      Check if the request can manage admin resources.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="null" />

        <PyParameter name="&#x22;admin_id&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;environment&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;require_auth&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;filter_datasets&#x22;" type="&#x22;(request, dataset_ids, action=_ACTION_DATASET_READ, environment=None, require_auth=True) -> list[str]&#x22;">
      Filter a list of dataset IDs to only those the principal can access.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="null" />

        <PyParameter name="&#x22;dataset_ids&#x22;" type="&#x22;list[str]&#x22;" value="null" />

        <PyParameter name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="&#x22;_ACTION_DATASET_READ&#x22;" />

        <PyParameter name="&#x22;environment&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;require_auth&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;list[str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_log_deny&#x22;" type="&#x22;(principal, action, resource, decision) -> None&#x22;">
      Log authorization denial for auditing.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;principal&#x22;" type="&#x22;Principal&#x22;" value="null" />

        <PyParameter name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;resource&#x22;" type="&#x22;ResourceRef&#x22;" value="null" />

        <PyParameter name="&#x22;decision&#x22;" type="&#x22;AuthorizationDecision&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
