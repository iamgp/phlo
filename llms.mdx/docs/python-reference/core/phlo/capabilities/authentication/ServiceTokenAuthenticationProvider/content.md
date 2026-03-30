# ServiceTokenAuthenticationProvider (/docs/python-reference/core/phlo/capabilities/authentication/ServiceTokenAuthenticationProvider)



Service principal/token authentication provider.

This provider validates service accounts used for automation
and service-to-service authentication.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, service_tokens=None)&#x22;">
  <PySourceCode>
    ```python
    def __init__(
        self,
        service_tokens: dict[str, dict[str, Any]] | None = None,
    ):
        self._service_tokens = service_tokens or {}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;service_tokens&#x22;" type="&#x22;dict[str, dict[str, Any]] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;authenticate&#x22;" type="&#x22;(self, request_context) -> AuthResult&#x22;">
  Authenticate using service token.

  <PySourceCode>
    ```python
    def authenticate(self, request_context: RequestContext) -> AuthResult:
        """Authenticate using service token."""
        auth_header = request_context.headers.get("authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            session = self.validate_token(token)
            if session:
                return AuthResult(
                    authenticated=True,
                    principal=session.principal,
                    session=session,
                    reason_code="authenticated",
                )

        return AuthResult(
            authenticated=False,
            reason_code="missing_credentials",
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;request_context&#x22;" type="&#x22;RequestContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.AuthResult&#x22;" />
</PyFunction>

<PyFunction name="&#x22;current_principal&#x22;" type="&#x22;(self, request_context) -> AuthPrincipal | None&#x22;">
  Get current principal from request context.

  <PySourceCode>
    ```python
    def current_principal(self, request_context: RequestContext) -> AuthPrincipal | None:
        """Get current principal from request context."""
        result = self.authenticate(request_context)
        return result.principal
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;request_context&#x22;" type="&#x22;RequestContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.AuthPrincipal | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;validate_token&#x22;" type="&#x22;(self, token) -> AuthenticatedSession | None&#x22;">
  Validate a service token.

  <PySourceCode>
    ```python
    def validate_token(self, token: str) -> AuthenticatedSession | None:
        """Validate a service token."""
        if token in self._service_tokens:
            service_data = self._service_tokens[token]
            principal = AuthPrincipal(
                subject=service_data.get("subject", token),
                principal_type="service",
                issuer=service_data.get("issuer"),
                email=service_data.get("email"),
                groups=tuple(service_data.get("groups", [])),
                claims=service_data.get("claims", {}),
                attributes=service_data.get("attributes", {}),
            )
            return AuthenticatedSession(
                principal=principal,
                auth_method="bearer_token",
                provider_name="service_token",
                session_id=secrets.token_urlsafe(32),
                attributes={"service": "true"},
            )
        return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;token&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.AuthenticatedSession | None&#x22;" />
</PyFunction>
