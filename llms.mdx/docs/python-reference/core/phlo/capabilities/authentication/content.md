# authentication (/docs/python-reference/core/phlo/capabilities/authentication)



Default authentication provider capability providers.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;REASON_CODES&#x22;" type="null" value="&#x22;{'authenticated': 'Authentication succeeded', 'missing_credentials': 'No credentials provided', 'invalid_token': 'Token validation failed', 'expired_session': 'Session has expired', 'provider_unavailable': 'Authentication provider unavailable', 'invalid_identity_payload': 'Identity payload malformed', 'ambiguous_provider': 'Multiple providers installed, explicit selection required', 'unsupported_flow': 'Requested flow not supported by provider'}&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;StaticAuthenticationProvider&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/authentication/StaticAuthenticationProvider&#x22;" />

      <Card title="&#x22;ProxyAuthenticationProvider&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/authentication/ProxyAuthenticationProvider&#x22;" />

      <Card title="&#x22;ServiceTokenAuthenticationProvider&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/authentication/ServiceTokenAuthenticationProvider&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_log_auth_event&#x22;" type="&#x22;(event_type, principal, reason_code, provider_name, auth_method=None, **extra) -> None&#x22;">
      Log authentication event for audit purposes.

      <PySourceCode>
        ```python
        def _log_auth_event(
            event_type: str,
            principal: AuthPrincipal | None,
            reason_code: str,
            provider_name: str,
            auth_method: str | None = None,
            **extra: Any,
        ) -> None:
            """Log authentication event for audit purposes."""
            log_args = {
                "event_type": event_type,
                "reason_code": reason_code,
                "provider": provider_name,
            }
            if principal:
                log_args["subject"] = principal.subject
                log_args["principal_type"] = principal.principal_type
                if principal.issuer:
                    log_args["issuer"] = principal.issuer
                if principal.email:
                    log_args["email"] = principal.email
            if auth_method:
                log_args["auth_method"] = auth_method
            log_args.update(extra)

            if event_type == "authentication_success":
                logger.info("authentication_success", **log_args)
            else:
                logger.warning(f"authentication_{event_type.replace('_', '_')}", **log_args)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;event_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;principal&#x22;" type="&#x22;AuthPrincipal | None&#x22;" value="null" />

        <PyParameter name="&#x22;reason_code&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;provider_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;auth_method&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;extra&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_load_static_config&#x22;" type="&#x22;() -> tuple[dict[str, dict[str, Any]], bool]&#x22;">
      Load static authentication configuration from environment.

      <PySourceCode>
        ```python
        def _load_static_config() -> tuple[dict[str, dict[str, Any]], bool]:
            """Load static authentication configuration from environment."""
            static_users = {}
            dev_mode = os.environ.get("PHLO_AUTH_DEV_MODE", "").lower() in ("1", "true", "yes")

            users_json = os.environ.get("PHLO_AUTH_STATIC_USERS")
            if users_json:
                with suppress(json.JSONDecodeError):
                    static_users = json.loads(users_json)

            return static_users, dev_mode
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;tuple[dict[str, dict[str, typing.Any]], bool]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_load_proxy_config&#x22;" type="&#x22;() -> dict[str, Any]&#x22;">
      Load proxy authentication configuration from environment.

      <PySourceCode>
        ```python
        def _load_proxy_config() -> dict[str, Any]:
            """Load proxy authentication configuration from environment."""
            config = {}

            trusted = os.environ.get("PHLO_AUTH_PROXY_TRUSTED_PROXIES")
            if trusted:
                config["trusted_proxies"] = [p.strip() for p in trusted.split(",")]

            header_subject = os.environ.get("PHLO_AUTH_PROXY_HEADER_SUBJECT")
            if header_subject:
                config["header_subject"] = header_subject

            return config
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_load_service_token_config&#x22;" type="&#x22;() -> dict[str, dict[str, Any]]&#x22;">
      Load service token configuration from environment.

      <PySourceCode>
        ```python
        def _load_service_token_config() -> dict[str, dict[str, Any]]:
            """Load service token configuration from environment."""
            service_tokens = {}

            tokens_json = os.environ.get("PHLO_AUTH_SERVICE_TOKENS")
            if tokens_json:
                with suppress(json.JSONDecodeError):
                    service_tokens = json.loads(tokens_json)

            return service_tokens
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dict[str, dict[str, typing.Any]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_default_capability_providers&#x22;" type="&#x22;() -> None&#x22;">
      Register authentication providers only when explicitly enabled via config.

      Authentication providers are security-sensitive and must be explicitly
      enabled via environment variables, not auto-registered on startup.

      <PySourceCode>
        ```python
        def register_default_capability_providers() -> None:
            """Register authentication providers only when explicitly enabled via config.

            Authentication providers are security-sensitive and must be explicitly
            enabled via environment variables, not auto-registered on startup.
            """
            static_users, dev_mode = _load_static_config()
            if static_users or dev_mode or os.environ.get("PHLO_AUTH_STATIC_ENABLED"):
                register_authentication_provider(
                    AuthenticationProviderSpec(
                        name="static",
                        provider=StaticAuthenticationProvider(
                            static_users=static_users,
                            dev_mode=dev_mode,
                        ),
                        metadata={
                            "auth_method": "static",
                            "supports_browser_login": False,
                            "supports_proxy_auth": False,
                            "supports_service_tokens": True,
                            "dev_mode": dev_mode,
                        },
                        support=CapabilitySupport(
                            supports_permissions=False,
                            supports_attributes=True,
                        ),
                    )
                )

            proxy_config = _load_proxy_config()
            if proxy_config or os.environ.get("PHLO_AUTH_PROXY_ENABLED"):
                register_authentication_provider(
                    AuthenticationProviderSpec(
                        name="proxy",
                        provider=ProxyAuthenticationProvider(**proxy_config),
                        metadata={
                            "auth_method": "proxy",
                            "supports_browser_login": False,
                            "supports_proxy_auth": True,
                            "supports_service_tokens": False,
                        },
                        support=CapabilitySupport(
                            supports_permissions=False,
                            supports_attributes=True,
                        ),
                    )
                )

            service_tokens = _load_service_token_config()
            if service_tokens or os.environ.get("PHLO_AUTH_SERVICE_ENABLED"):
                register_authentication_provider(
                    AuthenticationProviderSpec(
                        name="service_token",
                        provider=ServiceTokenAuthenticationProvider(
                            service_tokens=service_tokens,
                        ),
                        metadata={
                            "auth_method": "bearer_token",
                            "supports_browser_login": False,
                            "supports_proxy_auth": False,
                            "supports_service_tokens": True,
                        },
                        support=CapabilitySupport(
                            supports_permissions=False,
                            supports_attributes=True,
                        ),
                    )
                )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
