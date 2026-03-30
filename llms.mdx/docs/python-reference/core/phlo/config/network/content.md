# network (/docs/python-reference/core/phlo/config/network)



Host resolution helpers for Docker ↔ host portability.

When phlo CLI commands run on the host machine, Docker-internal hostnames
(`postgres`, `minio`, `trino`, etc.) are unreachable.  These helpers
detect that situation and transparently fall back to `localhost` with the
appropriate exposed port.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;structlog.get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;resolve_host&#x22;" type="&#x22;(host, port, *, port_env_var=None) -> tuple[str, int]&#x22;">
      Resolve a service hostname, falling back to localhost if DNS fails.

      <PySourceCode>
        ```python
        def resolve_host(host: str, port: int, *, port_env_var: str | None = None) -> tuple[str, int]:
            """Resolve a service hostname, falling back to localhost if DNS fails.

            Args:
                host: Service hostname (may be a Docker-internal name).
                port: Default port for the service.
                port_env_var: Optional environment variable that holds the host-exposed port.

            Returns:
                ``(host, port)`` tuple, resolved to ``localhost`` when the original
                hostname cannot be reached from the current environment.

            """
            if host in _LOCALHOST:
                return host, port

            try:
                socket.gethostbyname(host)
                return host, port
            except socket.gaierror:
                resolved_port = int(os.environ.get(port_env_var, str(port))) if port_env_var else port
                logger.debug(
                    "host_resolved_to_localhost",
                    original_host=host,
                    original_port=port,
                    resolved_port=resolved_port,
                )
                return "localhost", resolved_port
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;host&#x22;" type="&#x22;str&#x22;" value="undefined">
          Service hostname (may be a Docker-internal name).
        </PyParameter>

        <PyParameter name="&#x22;port&#x22;" type="&#x22;int&#x22;" value="undefined">
          Default port for the service.
        </PyParameter>

        <PyParameter name="&#x22;port_env_var&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional environment variable that holds the host-exposed port.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        `(host, port)` tuple, resolved to `localhost` when the original
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;resolve_url&#x22;" type="&#x22;(url, *, port_env_var=None) -> str&#x22;">
      Resolve a service URL, falling back to localhost if the hostname is unreachable.

      <PySourceCode>
        ```python
        def resolve_url(url: str, *, port_env_var: str | None = None) -> str:
            """Resolve a service URL, falling back to localhost if the hostname is unreachable.

            Args:
                url: Full URL that may reference a Docker-internal hostname.
                port_env_var: Optional environment variable for the host-exposed port.

            Returns:
                Resolved URL with ``localhost`` substituted when the original host
                cannot be resolved.

            """
            if not url:
                return url

            parsed = urlsplit(url)
            host = parsed.hostname
            if not host or host in _LOCALHOST:
                return url

            try:
                socket.gethostbyname(host)
                return url
            except socket.gaierror:
                original_port = parsed.port
                resolved_port = (
                    int(os.environ.get(port_env_var, str(original_port or 80)))
                    if port_env_var
                    else original_port
                )
                netloc = f"localhost:{resolved_port}" if resolved_port else "localhost"
                resolved = urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))
                logger.debug(
                    "url_resolved_to_localhost",
                    original_url=url,
                    resolved_url=resolved,
                )
                return resolved
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;url&#x22;" type="&#x22;str&#x22;" value="undefined">
          Full URL that may reference a Docker-internal hostname.
        </PyParameter>

        <PyParameter name="&#x22;port_env_var&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional environment variable for the host-exposed port.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Resolved URL with `localhost` substituted when the original host
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
