# ProxyAuthenticationProvider (/docs/python-reference/core/phlo/capabilities/authentication/ProxyAuthenticationProvider)



Reverse-proxy asserted identity authentication provider.

This provider validates requests from trusted reverse proxies that
assert user identity through headers. It uses CIDR notation for
trusted proxy configuration.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, trusted_proxies=None, header_subject='X-Remote-User', header_email='X-Remote-Email', header_groups='X-Remote-Groups')&#x22;">
  <PySourceCode>
    ```python
    def __init__(
        self,
        trusted_proxies: list[str] | None = None,
        header_subject: str = "X-Remote-User",
        header_email: str = "X-Remote-Email",
        header_groups: str = "X-Remote-Groups",
    ):
        self._trusted_networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
        self._trusted_hosts: set[str] = set()
        for proxy in trusted_proxies or ["127.0.0.1/32", "::1/128"]:
            try:
                if "/" in proxy:
                    network = ipaddress.ip_network(proxy, strict=False)
                    self._trusted_networks.append(network)
                else:
                    self._trusted_hosts.add(proxy)
            except ValueError:
                logger.warning("invalid_trusted_proxy_config", proxy=proxy)
        self._header_subject = header_subject.lower()
        self._header_email = header_email.lower()
        self._header_groups = header_groups.lower()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;trusted_proxies&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;header_subject&#x22;" type="&#x22;str&#x22;" value="&#x22;'X-Remote-User'&#x22;" />

    <PyParameter name="&#x22;header_email&#x22;" type="&#x22;str&#x22;" value="&#x22;'X-Remote-Email'&#x22;" />

    <PyParameter name="&#x22;header_groups&#x22;" type="&#x22;str&#x22;" value="&#x22;'X-Remote-Groups'&#x22;" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;_is_from_trusted_proxy&#x22;" type="&#x22;(self, request_context) -> bool&#x22;">
  Check if request came from a trusted proxy using CIDR matching.

  <PySourceCode>
    ```python
    def _is_from_trusted_proxy(self, request_context: RequestContext) -> bool:
        """Check if request came from a trusted proxy using CIDR matching."""
        remote_addr = request_context.remote_addr
        if remote_addr is None:
            return False
        if remote_addr in self._trusted_hosts:
            return True
        try:
            addr = ipaddress.ip_address(remote_addr)
            for network in self._trusted_networks:
                if addr in network:
                    return True
        except ValueError:
            pass
        return False
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;request_context&#x22;" type="&#x22;RequestContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;authenticate&#x22;" type="&#x22;(self, request_context) -> AuthResult&#x22;">
  Authenticate using proxy-asserted identity.

  <PySourceCode>
    ```python
    def authenticate(self, request_context: RequestContext) -> AuthResult:
        """Authenticate using proxy-asserted identity."""
        if not self._is_from_trusted_proxy(request_context):
            _log_auth_event(
                "failure",
                None,
                "invalid_identity_payload",
                "proxy",
                auth_method="proxy",
                path=request_context.path,
                remote_addr=request_context.remote_addr,
                reason="untrusted_proxy",
            )
            return AuthResult(
                authenticated=False,
                reason_code="invalid_identity_payload",
            )

        subject = request_context.headers.get(self._header_subject)
        if not subject:
            _log_auth_event(
                "failure",
                None,
                "missing_credentials",
                "proxy",
                auth_method="proxy",
                path=request_context.path,
                remote_addr=request_context.remote_addr,
            )
            return AuthResult(
                authenticated=False,
                reason_code="missing_credentials",
            )

        email = request_context.headers.get(self._header_email)
        groups_raw = request_context.headers.get(self._header_groups, "")
        groups = tuple(g.strip() for g in groups_raw.split(",") if g.strip())

        principal = AuthPrincipal(
            subject=subject,
            principal_type="user",
            email=email,
            groups=groups,
            attributes={"source": "proxy"},
        )

        session = AuthenticatedSession(
            principal=principal,
            auth_method="proxy",
            provider_name="proxy",
            attributes={"remote_addr": request_context.remote_addr or "unknown"},
        )

        _log_auth_event(
            "success",
            principal,
            "authenticated",
            "proxy",
            auth_method="proxy",
            path=request_context.path,
            remote_addr=request_context.remote_addr,
        )

        return AuthResult(
            authenticated=True,
            principal=principal,
            session=session,
            reason_code="authenticated",
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
  Get current principal from proxy headers.

  <PySourceCode>
    ```python
    def current_principal(self, request_context: RequestContext) -> AuthPrincipal | None:
        """Get current principal from proxy headers."""
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
  Validate a bearer token (not supported in proxy provider).

  <PySourceCode>
    ```python
    def validate_token(self, token: str) -> AuthenticatedSession | None:
        """Validate a bearer token (not supported in proxy provider)."""
        return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;token&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.AuthenticatedSession | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;authenticate_proxy_identity&#x22;" type="&#x22;(self, request_context) -> AuthResult&#x22;">
  Authenticate proxy-asserted identity (explicit flow).

  <PySourceCode>
    ```python
    def authenticate_proxy_identity(self, request_context: RequestContext) -> AuthResult:
        """Authenticate proxy-asserted identity (explicit flow)."""
        return self.authenticate(request_context)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;request_context&#x22;" type="&#x22;RequestContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.AuthResult&#x22;" />
</PyFunction>
