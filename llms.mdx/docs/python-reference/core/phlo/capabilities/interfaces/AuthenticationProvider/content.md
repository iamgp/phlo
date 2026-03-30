# AuthenticationProvider (/docs/python-reference/core/phlo/capabilities/interfaces/AuthenticationProvider)



Protocol for authentication providers.

Every provider must implement the mandatory interface.
Optional browser flows may raise NotImplementedError if not supported.

Functions [#functions]

<PyFunction name="&#x22;authenticate&#x22;" type="&#x22;(self, request_context) -> AuthResult&#x22;">
  Authenticate a request and return the result.

  <PySourceCode>
    ```python
    def authenticate(self, request_context: RequestContext) -> AuthResult:
        """Authenticate a request and return the result."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;request_context&#x22;" type="&#x22;RequestContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.AuthResult&#x22;" />
</PyFunction>

<PyFunction name="&#x22;current_principal&#x22;" type="&#x22;(self, request_context) -> AuthPrincipal | None&#x22;">
  Get the current principal from an already-authenticated request.

  <PySourceCode>
    ```python
    def current_principal(self, request_context: RequestContext) -> AuthPrincipal | None:
        """Get the current principal from an already-authenticated request."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;request_context&#x22;" type="&#x22;RequestContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.AuthPrincipal | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;validate_token&#x22;" type="&#x22;(self, token) -> AuthenticatedSession | None&#x22;">
  Validate a bearer token and return session if valid.

  <PySourceCode>
    ```python
    def validate_token(self, token: str) -> AuthenticatedSession | None:
        """Validate a bearer token and return session if valid."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;token&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.AuthenticatedSession | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;start_login&#x22;" type="&#x22;(self) -> BrowserLoginStart&#x22;">
  Start a browser-based login flow (optional).

  <PySourceCode>
    ```python
    def start_login(self) -> BrowserLoginStart:
        """Start a browser-based login flow (optional)."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.BrowserLoginStart&#x22;" />
</PyFunction>

<PyFunction name="&#x22;finish_login&#x22;" type="&#x22;(self, request_context) -> AuthResult&#x22;">
  Finish a browser-based login flow (optional).

  <PySourceCode>
    ```python
    def finish_login(self, request_context: RequestContext) -> AuthResult:
        """Finish a browser-based login flow (optional)."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;request_context&#x22;" type="&#x22;RequestContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.AuthResult&#x22;" />
</PyFunction>

<PyFunction name="&#x22;logout&#x22;" type="&#x22;(self, request_context) -> LogoutResult&#x22;">
  Log out the current user (optional).

  <PySourceCode>
    ```python
    def logout(self, request_context: RequestContext) -> LogoutResult:
        """Log out the current user (optional)."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;request_context&#x22;" type="&#x22;RequestContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.LogoutResult&#x22;" />
</PyFunction>

<PyFunction name="&#x22;exchange_token&#x22;" type="&#x22;(self, token) -> AuthenticatedSession | None&#x22;">
  Exchange one token type for another (optional).

  <PySourceCode>
    ```python
    def exchange_token(self, token: str) -> AuthenticatedSession | None:
        """Exchange one token type for another (optional)."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;token&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.AuthenticatedSession | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;authenticate_proxy_identity&#x22;" type="&#x22;(self, request_context) -> AuthResult&#x22;">
  Authenticate reverse-proxy asserted identity (optional).

  <PySourceCode>
    ```python
    def authenticate_proxy_identity(self, request_context: RequestContext) -> AuthResult:
        """Authenticate reverse-proxy asserted identity (optional)."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;request_context&#x22;" type="&#x22;RequestContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.AuthResult&#x22;" />
</PyFunction>
