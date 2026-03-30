# StaticAuthenticationProvider (/docs/python-reference/core/phlo/capabilities/authentication/StaticAuthenticationProvider)



Static/local development authentication provider.

This provider is intended for development and testing only.
It validates against configured static users or always succeeds
when explicitly enabled in development mode.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, static_users=None, dev_mode=False)&#x22;">
  <PySourceCode>
    ```python
    def __init__(
        self,
        static_users: dict[str, dict[str, Any]] | None = None,
        dev_mode: bool = False,
    ):
        self._static_users = static_users or {}
        self._dev_mode = dev_mode
        self._sessions: dict[str, AuthenticatedSession] = {}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;static_users&#x22;" type="&#x22;dict[str, dict[str, Any]] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;dev_mode&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;authenticate&#x22;" type="&#x22;(self, request_context) -> AuthResult&#x22;">
  Authenticate using static credentials or dev mode.

  <PySourceCode>
    ```python
    def authenticate(self, request_context: RequestContext) -> AuthResult:
        """Authenticate using static credentials or dev mode."""
        auth_header = request_context.headers.get("authorization", "")
        cookie_session = request_context.cookies.get("phlo_session")

        if cookie_session and cookie_session in self._sessions:
            session = self._sessions[cookie_session]
            if self._is_session_valid(session):
                _log_auth_event(
                    "success",
                    session.principal,
                    "authenticated",
                    "static",
                    auth_method="session",
                    path=request_context.path,
                )
                return AuthResult(
                    authenticated=True,
                    principal=session.principal,
                    session=session,
                    reason_code="authenticated",
                )
            del self._sessions[cookie_session]

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            session = self.validate_token(token)
            if session:
                _log_auth_event(
                    "success",
                    session.principal,
                    "authenticated",
                    "static",
                    auth_method="bearer_token",
                    path=request_context.path,
                )
                return AuthResult(
                    authenticated=True,
                    principal=session.principal,
                    session=session,
                    reason_code="authenticated",
                )
            _log_auth_event(
                "failure",
                None,
                "invalid_token",
                "static",
                auth_method="bearer_token",
                path=request_context.path,
            )

        if self._dev_mode:
            dev_principal = AuthPrincipal(
                subject="dev_user",
                principal_type="user",
                email="dev@localhost",
                groups=("admin",),
                attributes={"mode": "development"},
            )
            session = AuthenticatedSession(
                principal=dev_principal,
                auth_method="static",
                provider_name="static",
                session_id=secrets.token_urlsafe(32),
                attributes={"mode": "development"},
            )
            _log_auth_event(
                "success",
                dev_principal,
                "authenticated",
                "static",
                auth_method="static",
                path=request_context.path,
            )
            return AuthResult(
                authenticated=True,
                principal=dev_principal,
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
  Validate a bearer token.

  <PySourceCode>
    ```python
    def validate_token(self, token: str) -> AuthenticatedSession | None:
        """Validate a bearer token."""
        if token in self._static_users:
            user_data = self._static_users[token]
            principal = AuthPrincipal(
                subject=user_data.get("subject", token),
                principal_type=user_data.get("principal_type", "user"),
                email=user_data.get("email"),
                groups=tuple(user_data.get("groups", [])),
                claims=user_data.get("claims", {}),
                attributes=user_data.get("attributes", {}),
            )
            return AuthenticatedSession(
                principal=principal,
                auth_method="bearer_token",
                provider_name="static",
                session_id=secrets.token_urlsafe(32),
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

<PyFunction name="&#x22;start_login&#x22;" type="&#x22;(self) -> BrowserLoginStart&#x22;">
  Start login flow (not supported in static provider).

  <PySourceCode>
    ```python
    def start_login(self) -> BrowserLoginStart:
        """Start login flow (not supported in static provider)."""
        raise NotImplementedError("Static provider does not support browser login")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.BrowserLoginStart&#x22;" />
</PyFunction>

<PyFunction name="&#x22;finish_login&#x22;" type="&#x22;(self, request_context) -> AuthResult&#x22;">
  Finish login flow (not supported in static provider).

  <PySourceCode>
    ```python
    def finish_login(self, request_context: RequestContext) -> AuthResult:
        """Finish login flow (not supported in static provider)."""
        raise NotImplementedError("Static provider does not support browser login")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;request_context&#x22;" type="&#x22;RequestContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.AuthResult&#x22;" />
</PyFunction>

<PyFunction name="&#x22;logout&#x22;" type="&#x22;(self, request_context) -> LogoutResult&#x22;">
  Log out the current user.

  <PySourceCode>
    ```python
    def logout(self, request_context: RequestContext) -> LogoutResult:
        """Log out the current user."""
        cookie_session = request_context.cookies.get("phlo_session")
        if cookie_session and cookie_session in self._sessions:
            del self._sessions[cookie_session]
        return LogoutResult(success=True)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;request_context&#x22;" type="&#x22;RequestContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.LogoutResult&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_is_session_valid&#x22;" type="&#x22;(self, session) -> bool&#x22;">
  Check if session is still valid.

  <PySourceCode>
    ```python
    def _is_session_valid(self, session: AuthenticatedSession) -> bool:
        """Check if session is still valid."""
        if session.expires_at is None:
            return True
        return datetime.now(timezone.utc) < session.expires_at  # noqa: UP017
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;session&#x22;" type="&#x22;AuthenticatedSession&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>
