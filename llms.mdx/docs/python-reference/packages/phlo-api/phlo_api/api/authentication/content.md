# authentication (/docs/python-reference/packages/phlo-api/phlo_api/api/authentication)



Authentication helpers for phlo-api.

This module provides authentication capability integration for FastAPI routes.
It bridges the phlo capabilities system with FastAPI request handling, enabling
flexible authentication through pluggable providers.

Key Functions:
get\_authentication\_provider: Resolve the configured authentication provider.
require\_authentication\_provider: Resolve provider or raise if unavailable.
authenticate\_request: Authenticate a FastAPI request.
get\_request\_principal: Get the authenticated principal from a request.
require\_principal: Get principal or raise HTTP 401.

Environment Variables:
PHLO\_AUTHENTICATION\_PROVIDER: Name of the authentication provider to use.
Required when multiple providers are installed.

Example:
Using authentication in a FastAPI route:

.. code-block:: python

from fastapi import Request
from phlo\_api.api.authentication import require\_principal

@app.get("/protected")
async def protected\_route(request: Request):
principal = require\_principal(request)
return \{"user": principal.subject}

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_authentication_provider&#x22;" type="&#x22;() -> AuthenticationProvider | None&#x22;">
      Resolve the authentication provider capability.

      Returns None if no provider is configured. Raises when multiple providers
      are installed without explicit selection.

      <PySourceCode>
        ```python
        def get_authentication_provider() -> AuthenticationProvider | None:
            """Resolve the authentication provider capability.

            Returns None if no provider is configured. Raises when multiple providers
            are installed without explicit selection.

            Args:
                None: No arguments required.

            Returns:
                AuthenticationProvider instance, or None if not configured.

            Raises:
                RuntimeError: If the configured provider is not registered, or if multiple
                    providers are available without explicit selection.

            """
            provider_name = os.environ.get(_AUTHENTICATION_PROVIDER_ENV)
            result = resolve_capability("authentication_provider", provider_name)
            if provider_name and result is None:
                raise RuntimeError(
                    f"Authentication provider {provider_name!r} is not registered. "
                    f"Set {_AUTHENTICATION_PROVIDER_ENV} to a valid provider name."
                )

            if result is None:
                available_providers = list_capabilities("authentication_provider")
                if not available_providers:
                    logger.debug("no_authentication_provider_configured")
                    return None
                if provider_name is None and len(available_providers) > 1:
                    raise RuntimeError(
                        "Multiple authentication providers are registered. "
                        f"Set {_AUTHENTICATION_PROVIDER_ENV} to one of: {', '.join(sorted(available_providers))}."
                    )
                logger.debug("no_authentication_provider_configured")
                return None
            return result.provider
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;AuthenticationProvider | None&#x22;">
        AuthenticationProvider instance, or None if not configured.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;require_authentication_provider&#x22;" type="&#x22;() -> AuthenticationProvider&#x22;">
      Resolve the authentication provider or raise if not available.

      <PySourceCode>
        ```python
        def require_authentication_provider() -> AuthenticationProvider:
            """Resolve the authentication provider or raise if not available.

            Args:
                None: No arguments required.

            Returns:
                AuthenticationProvider instance.

            Raises:
                RuntimeError: If no authentication provider is configured.

            """
            provider = get_authentication_provider()
            if provider is None:
                raise RuntimeError("Authentication provider not configured")
            return provider
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.capabilities.AuthenticationProvider&#x22;">
        AuthenticationProvider instance.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;create_request_context&#x22;" type="&#x22;(request) -> RequestContext&#x22;">
      Create a RequestContext from a FastAPI request.

      Extracts headers, cookies, query params, and connection metadata from
      the incoming request for use by authentication providers.

      <PySourceCode>
        ```python
        def create_request_context(request: Request) -> RequestContext:
            """Create a RequestContext from a FastAPI request.

            Extracts headers, cookies, query params, and connection metadata from
            the incoming request for use by authentication providers.

            Args:
                request: The FastAPI request object.

            Returns:
                RequestContext populated with request metadata.

            Raises:
                None: No exceptions raised directly.

            """
            headers_dict: dict[str, str] = {}
            for key, value in request.headers.items():
                headers_dict[key.lower()] = value
            cookies_dict = dict(request.cookies)
            query_params_dict = dict(request.query_params)

            return RequestContext(
                headers=headers_dict,
                cookies=cookies_dict,
                query_params=query_params_dict,
                method=request.method,
                path=request.url.path,
                remote_addr=request.client.host if request.client else None,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="undefined">
          The FastAPI request object.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo.capabilities.RequestContext&#x22;">
        RequestContext populated with request metadata.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;authenticate_request&#x22;" type="&#x22;(request) -> AuthResult&#x22;">
      Authenticate a request using the configured authentication provider.

      Returns an AuthResult that indicates whether authentication succeeded.
      Caches the result in request.state to avoid duplicate authentication.

      <PySourceCode>
        ```python
        def authenticate_request(request: Request) -> AuthResult:
            """Authenticate a request using the configured authentication provider.

            Returns an AuthResult that indicates whether authentication succeeded.
            Caches the result in request.state to avoid duplicate authentication.

            Args:
                request: The FastAPI request object.

            Returns:
                AuthResult with authentication status and principal (if successful).

            Raises:
                None: No exceptions raised directly.

            """
            if hasattr(request.state, _AUTH_RESULT_CACHE_KEY):
                return request.state[_AUTH_RESULT_CACHE_KEY]

            provider = get_authentication_provider()
            if provider is None:
                result = AuthResult(
                    authenticated=False,
                    reason_code="provider_unavailable",
                )
                request.state[_AUTH_RESULT_CACHE_KEY] = result
                return result

            request_context = create_request_context(request)
            result = provider.authenticate(request_context)
            request.state[_AUTH_RESULT_CACHE_KEY] = result
            return result
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="undefined">
          The FastAPI request object.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo.capabilities.AuthResult&#x22;">
        AuthResult with authentication status and principal (if successful).
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_request_principal&#x22;" type="&#x22;(request) -> AuthPrincipal | None&#x22;">
      Get the authenticated principal from the request.

      Returns None if no authentication provider is configured or authentication failed.
      Caches the result in request.state to avoid duplicate authentication.

      <PySourceCode>
        ```python
        def get_request_principal(request: Request) -> AuthPrincipal | None:
            """Get the authenticated principal from the request.

            Returns None if no authentication provider is configured or authentication failed.
            Caches the result in request.state to avoid duplicate authentication.

            Args:
                request: The FastAPI request object.

            Returns:
                AuthPrincipal if authenticated, None otherwise.

            Raises:
                None: No exceptions raised directly.

            """
            if hasattr(request.state, _AUTH_PRINCIPAL_CACHE_KEY):
                return request.state[_AUTH_PRINCIPAL_CACHE_KEY]

            provider = get_authentication_provider()
            if provider is None:
                request.state[_AUTH_PRINCIPAL_CACHE_KEY] = None
                return None

            request_context = create_request_context(request)
            principal = provider.current_principal(request_context)
            request.state[_AUTH_PRINCIPAL_CACHE_KEY] = principal
            return principal
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="undefined">
          The FastAPI request object.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;AuthPrincipal | None&#x22;">
        AuthPrincipal if authenticated, None otherwise.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;require_principal&#x22;" type="&#x22;(request) -> AuthPrincipal&#x22;">
      Get the authenticated principal from the request or raise 401.

      Raises HTTPException 401 if authentication failed or no provider is configured.
      Uses cached result from request.state if available.

      <PySourceCode>
        ```python
        def require_principal(request: Request) -> AuthPrincipal:
            """Get the authenticated principal from the request or raise 401.

            Raises HTTPException 401 if authentication failed or no provider is configured.
            Uses cached result from request.state if available.

            Args:
                request: The FastAPI request object.

            Returns:
                AuthPrincipal if authentication succeeds.

            Raises:
                HTTPException: 401 if authentication fails or provider unavailable.

            """
            if hasattr(request.state, _AUTH_PRINCIPAL_CACHE_KEY):
                cached = request.state[_AUTH_PRINCIPAL_CACHE_KEY]
                if cached is not None:
                    return cached
                if cached is None and not hasattr(request.state, _AUTH_RESULT_CACHE_KEY):
                    raise HTTPException(
                        status_code=401,
                        detail={"error": "unauthorized", "reason": "no_auth_result"},
                    )

            if hasattr(request.state, _AUTH_RESULT_CACHE_KEY):
                result = request.state[_AUTH_RESULT_CACHE_KEY]
            else:
                provider = get_authentication_provider()
                if provider is None:
                    logger.warning("authentication_provider_not_configured")
                    raise HTTPException(
                        status_code=401,
                        detail={"error": "unauthorized", "reason": "provider_unavailable"},
                    )
                request_context = create_request_context(request)
                result = provider.authenticate(request_context)
                request.state[_AUTH_RESULT_CACHE_KEY] = result

            if not result.authenticated:
                logger.warning(
                    "authentication_failed",
                    reason_code=result.reason_code,
                    path=request.url.path,
                    method=request.method,
                )
                raise HTTPException(
                    status_code=401,
                    detail={"error": "unauthorized", "reason": result.reason_code},
                )

            if result.principal is None:
                raise HTTPException(
                    status_code=401,
                    detail={"error": "unauthorized", "reason": "invalid_identity_payload"},
                )

            request.state[_AUTH_PRINCIPAL_CACHE_KEY] = result.principal
            return result.principal
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="undefined">
          The FastAPI request object.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo.capabilities.AuthPrincipal&#x22;">
        AuthPrincipal if authentication succeeds.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;optional_authenticate&#x22;" type="&#x22;(request) -> AuthPrincipal | None&#x22;">
      Attempt to authenticate a request, returning None if not authenticated.

      Unlike require\_principal, this does not raise on authentication failure.
      Useful for routes that have different behavior for authenticated vs anonymous.

      <PySourceCode>
        ```python
        def optional_authenticate(request: Request) -> AuthPrincipal | None:
            """Attempt to authenticate a request, returning None if not authenticated.

            Unlike require_principal, this does not raise on authentication failure.
            Useful for routes that have different behavior for authenticated vs anonymous.

            Args:
                request: The FastAPI request object.

            Returns:
                AuthPrincipal if authentication succeeds, None otherwise.

            Raises:
                None: No exceptions raised directly.

            """
            provider = get_authentication_provider()
            if provider is None:
                return None

            request_context = create_request_context(request)
            result = provider.authenticate(request_context)

            if result.authenticated and result.principal is not None:
                return result.principal

            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="undefined">
          The FastAPI request object.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;AuthPrincipal | None&#x22;">
        AuthPrincipal if authentication succeeds, None otherwise.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_capabilities_metadata&#x22;" type="&#x22;() -> dict[str, Any]&#x22;">
      Get metadata about available authentication capabilities.

      Returns a dictionary with available providers, current provider setting,
      and environment variable information.

      <PySourceCode>
        ```python
        def get_capabilities_metadata() -> dict[str, Any]:
            """Get metadata about available authentication capabilities.

            Returns a dictionary with available providers, current provider setting,
            and environment variable information.

            Args:
                None: No arguments required.

            Returns:
                Dictionary with authentication capability metadata.

            Raises:
                None: No exceptions raised directly.

            """
            available_providers = list_capabilities("authentication_provider")
            current_provider = os.environ.get(_AUTHENTICATION_PROVIDER_ENV)

            return {
                "available_providers": available_providers,
                "current_provider": current_provider,
                "environment_variable": _AUTHENTICATION_PROVIDER_ENV,
            }
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary with authentication capability metadata.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
