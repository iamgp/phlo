# ports (/docs/python-reference/core/phlo/cli/commands/services/ports)



Ports command for showing service port mappings.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;PORT_PATTERN&#x22;" type="null" value="&#x22;re.compile('\\\\$\\\\{([^}:]+)(?::-([^}]*))?\\\\}:(\\\\d+)')&#x22;" />

<PyAttribute name="&#x22;DEFAULT_PORT_PATTERN&#x22;" type="null" value="&#x22;re.compile('\\\\$\\\\{([^}:]+):-(\\\\d+)\\\\}')&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PortMapping&#x22;" href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/ports/PortMapping&#x22;" />

      <Card title="&#x22;ComposePortSpec&#x22;" href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/ports/ComposePortSpec&#x22;" />

      <Card title="&#x22;TraefikContext&#x22;" href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/ports/TraefikContext&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_parse_compose_port&#x22;" type="&#x22;(port_str) -> tuple[str | None, str]&#x22;">
      Parse a compose port string into (env\_var, container\_port).

      Format: "$\{VAR:-default}:container" or "host:container"

      <PySourceCode>
        ```python
        def _parse_compose_port(port_str: str) -> tuple[str | None, str]:
            """Parse a compose port string into (env_var, container_port).

            Format: "${VAR:-default}:container" or "host:container"
            """
            spec = _parse_compose_port_spec(port_str)
            return (spec.env_var, spec.container_port)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;port_str&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;tuple[str | None, str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_parse_compose_port_spec&#x22;" type="&#x22;(port_str) -> ComposePortSpec&#x22;">
      Parse a compose port string into its env/literal host and container parts.

      <PySourceCode>
        ```python
        def _parse_compose_port_spec(port_str: str) -> ComposePortSpec:
            """Parse a compose port string into its env/literal host and container parts."""
            normalized = port_str.strip().strip("\"'")
            match = PORT_PATTERN.match(normalized)
            if match:
                return ComposePortSpec(
                    env_var=match.group(1),
                    host_port=match.group(2),
                    container_port=match.group(3),
                )

            if ":" in normalized:
                host_part, container_part = normalized.rsplit(":", 1)
                return ComposePortSpec(
                    env_var=None,
                    host_port=host_part.rsplit(":", 1)[-1],
                    container_port=container_part.split("/", 1)[0],
                )

            return ComposePortSpec(env_var=None, host_port=None, container_port=normalized)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;port_str&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.cli.commands.services.ports.ComposePortSpec&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_resolve_env_var&#x22;" type="&#x22;(env_var, env) -> str | None&#x22;">
      Resolve an environment variable from the loaded environment.

      <PySourceCode>
        ```python
        def _resolve_env_var(env_var: str | None, env: dict[str, str]) -> str | None:
            """Resolve an environment variable from the loaded environment."""
            if env_var is None:
                return None
            return env.get(env_var)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;env_var&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;env&#x22;" type="&#x22;dict[str, str]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_load_environment&#x22;" type="&#x22;(phlo_dir, config) -> dict[str, str]&#x22;">
      Load effective compose environment with standard Phlo precedence.

      <PySourceCode>
        ```python
        def _load_environment(phlo_dir: Path, config: dict[str, Any]) -> dict[str, str]:
            """Load effective compose environment with standard Phlo precedence."""
            env: dict[str, str] = {}

            env_file = phlo_dir / ".env"
            env_local_file = phlo_dir / ".env.local"

            for file_path in [env_file, env_local_file]:
                if file_path.exists():
                    parsed = parse_env_file(file_path)
                    env.update(parsed)

            env.update({k: str(v) for k, v in _get_env_overrides(config).items() if isinstance(k, str)})
            env.update(os.environ)

            return env
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;phlo_dir&#x22;" type="&#x22;Path&#x22;" value="null" />

        <PyParameter name="&#x22;config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_get_running_container_ports&#x22;" type="&#x22;(project_name) -> dict[str, list[dict]]&#x22;">
      Get published ports from running containers.

      <PySourceCode>
        ```python
        def _get_running_container_ports(project_name: str) -> dict[str, list[dict]]:
            """Get published ports from running containers."""
            try:
                result = run_command(
                    [
                        "docker",
                        "ps",
                        "--filter",
                        f"label=com.docker.compose.project={project_name}",
                        "--format",
                        "{{json .}}",
                    ],
                    check=False,
                )
                containers = {}
                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split("\n"):
                        info = json.loads(line)
                        service = None
                        for label in info.get("Labels", "").split(","):
                            if label.startswith("com.docker.compose.service="):
                                service = label.split("=", 1)[1]
                                break
                        if service:
                            ports_str = info.get("Ports", "")
                            port_mappings: list[dict[str, str]] = []
                            if ports_str:
                                for port_entry in ports_str.split(", "):
                                    if "->" in port_entry:
                                        host_part, container_part = port_entry.split("->")
                                        host_ip = (
                                            host_part.rsplit(":", 1)[0] if ":" in host_part else "0.0.0.0"
                                        )
                                        host_port = (
                                            host_part.rsplit(":", 1)[-1] if ":" in host_part else host_part
                                        )
                                        port_mappings.append(
                                            {
                                                "host_port": host_port,
                                                "host_ip": host_ip,
                                                "container_port": container_part,
                                            }
                                        )
                            containers[service] = {
                                "status": info.get("State", "running"),
                                "ports": port_mappings,
                            }
                return containers
            except Exception:
                logger.warning("docker_ps_failed", exc_info=True)
                return {}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, phlo.cli.commands.services.list[dict]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_get_runtime_host_port&#x22;" type="&#x22;(running_containers, service_name, container_port) -> int | None&#x22;">
      Return the live host port for a running container port mapping, if present.

      <PySourceCode>
        ```python
        def _get_runtime_host_port(
            running_containers: dict[str, Any],
            service_name: str,
            container_port: int,
        ) -> int | None:
            """Return the live host port for a running container port mapping, if present."""
            container_info = running_containers.get(service_name, {})
            for port_mapping in container_info.get("ports", []):
                container_value = str(port_mapping.get("container_port", "")).split("/", 1)[0]
                if container_value != str(container_port):
                    continue
                host_port = port_mapping.get("host_port")
                if host_port and str(host_port).isdigit():
                    return int(host_port)
            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;running_containers&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />

        <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;container_port&#x22;" type="&#x22;int&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;int | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_get_default_host_port&#x22;" type="&#x22;(port_str, port_spec) -> int | None&#x22;">
      Resolve a configured host port from a compose mapping when no runtime mapping exists.

      <PySourceCode>
        ```python
        def _get_default_host_port(port_str: str, port_spec: ComposePortSpec) -> int | None:
            """Resolve a configured host port from a compose mapping when no runtime mapping exists."""
            if port_spec.host_port and port_spec.host_port.isdigit():
                return int(port_spec.host_port)

            if port_spec.env_var:
                default_match = DEFAULT_PORT_PATTERN.search(port_str)
                if default_match:
                    return int(default_match.group(2))

            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;port_str&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;port_spec&#x22;" type="&#x22;ComposePortSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;int | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_resolve_host_port&#x22;" type="&#x22;(*, port_str, port_spec, service_name, container_port, env, running_containers) -> tuple[int | None, str, str | None]&#x22;">
      Resolve the effective host port for a service/container port pair.

      <PySourceCode>
        ```python
        def _resolve_host_port(
            *,
            port_str: str,
            port_spec: ComposePortSpec,
            service_name: str,
            container_port: int,
            env: dict[str, str],
            running_containers: dict[str, Any],
        ) -> tuple[int | None, str, str | None]:
            """Resolve the effective host port for a service/container port pair."""
            resolved_host_port: int | None = None
            source = "default"
            resolved_env_var: str | None = None

            resolved_host_port = _get_runtime_host_port(running_containers, service_name, container_port)
            if resolved_host_port is not None:
                return resolved_host_port, "runtime", None

            if port_spec.env_var:
                resolved_value = _resolve_env_var(port_spec.env_var, env)
                if resolved_value and resolved_value.isdigit():
                    return int(resolved_value), "env", port_spec.env_var

            resolved_host_port = _get_default_host_port(port_str, port_spec)
            if resolved_host_port is not None and port_spec.env_var is None and port_spec.host_port:
                source = "compose"

            return resolved_host_port, source, resolved_env_var
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;port_str&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;port_spec&#x22;" type="&#x22;ComposePortSpec&#x22;" value="null" />

        <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;container_port&#x22;" type="&#x22;int&#x22;" value="null" />

        <PyParameter name="&#x22;env&#x22;" type="&#x22;dict[str, str]&#x22;" value="null" />

        <PyParameter name="&#x22;running_containers&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;tuple[int | None, str, str | None]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_get_active_traefik_context&#x22;" type="&#x22;(services, env, running_containers, disabled_services, service_overrides) -> TraefikContext | None&#x22;">
      Return Traefik routing context when the proxy is available and running.

      <PySourceCode>
        ```python
        def _get_active_traefik_context(
            services: dict[str, ServiceDefinition],
            env: dict[str, str],
            running_containers: dict[str, Any],
            disabled_services: set[str],
            service_overrides: dict[str, Any],
        ) -> TraefikContext | None:
            """Return Traefik routing context when the proxy is available and running."""
            traefik_service = services.get("traefik")
            if traefik_service is None or "traefik" in disabled_services:
                return None

            if "traefik" not in running_containers:
                return None

            traefik_override = service_overrides.get("traefik", {})
            compose_ports = traefik_service.compose.get("ports", [])
            if isinstance(traefik_override, dict) and traefik_override.get("ports"):
                compose_ports = traefik_override["ports"]

            for port_str in compose_ports:
                port_spec = _parse_compose_port_spec(port_str)
                if port_spec.container_port != "80":
                    continue
                host_port, _, _ = _resolve_host_port(
                    port_str=port_str,
                    port_spec=port_spec,
                    service_name="traefik",
                    container_port=80,
                    env=env,
                    running_containers=running_containers,
                )
                if host_port is not None:
                    return TraefikContext(
                        domain=env.get("TRAEFIK_DOMAIN", "phlo.localhost"),
                        host_port=host_port,
                    )

            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;services&#x22;" type="&#x22;dict[str, ServiceDefinition]&#x22;" value="null" />

        <PyParameter name="&#x22;env&#x22;" type="&#x22;dict[str, str]&#x22;" value="null" />

        <PyParameter name="&#x22;running_containers&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />

        <PyParameter name="&#x22;disabled_services&#x22;" type="&#x22;set[str]&#x22;" value="null" />

        <PyParameter name="&#x22;service_overrides&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.cli.commands.services.ports.TraefikContext | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_get_traefik_routes&#x22;" type="&#x22;(service, traefik) -> dict[str, str]&#x22;">
      Extract Traefik routes from service labels. Returns \{container\_port: url}.

      <PySourceCode>
        ```python
        def _get_traefik_routes(
            service: ServiceDefinition,
            traefik: TraefikContext | None,
        ) -> dict[str, str]:
            """Extract Traefik routes from service labels. Returns {container_port: url}."""
            routes: dict[str, str] = {}
            if traefik is None:
                return routes

            labels = service.compose.get("labels", {})
            if not labels:
                return routes

            if labels.get("traefik.enable") != "true":
                return routes

            router_rule_pattern = re.compile(r"Host\(`([^`]+)`\)")

            router_hostnames: dict[str, str] = {}
            router_services: dict[str, str] = {}
            service_ports: dict[str, str] = {}

            for key, value in labels.items():
                key_str = str(key)

                if key_str.startswith("traefik.http.routers.") and ".rule" in key_str:
                    router_name = key_str.replace("traefik.http.routers.", "").replace(".rule", "")
                    match = router_rule_pattern.search(str(value))
                    if match:
                        hostname = match.group(1)
                        hostname = hostname.replace(
                            "${TRAEFIK_DOMAIN:-phlo.localhost}",
                            traefik.domain,
                        )
                        router_hostnames[router_name] = hostname

                if key_str.startswith("traefik.http.routers.") and ".service" in key_str:
                    router_name = key_str.replace("traefik.http.routers.", "").replace(".service", "")
                    router_services[router_name] = str(value)

                if key_str.startswith("traefik.http.services.") and ".loadbalancer.server.port" in key_str:
                    service_name = key_str.replace("traefik.http.services.", "").replace(
                        ".loadbalancer.server.port", ""
                    )
                    service_ports[service_name] = str(value)

            for router_name, hostname in router_hostnames.items():
                url = (
                    f"http://{hostname}"
                    if traefik.host_port == 80
                    else f"http://{hostname}:{traefik.host_port}"
                )

                traefik_svc_name = router_services.get(router_name, router_name)
                port = service_ports.get(traefik_svc_name)
                if port:
                    routes[port] = url
                    continue

                if router_services.get(router_name) == "api@internal":
                    routes["80"] = url

            return routes
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;service&#x22;" type="&#x22;ServiceDefinition&#x22;" value="null" />

        <PyParameter name="&#x22;traefik&#x22;" type="&#x22;TraefikContext | None&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_get_service_routes&#x22;" type="&#x22;(services, traefik) -> dict[str, dict[str, str]]&#x22;">
      Get all Traefik routes indexed by service name.

      <PySourceCode>
        ```python
        def _get_service_routes(
            services: dict[str, ServiceDefinition],
            traefik: TraefikContext | None,
        ) -> dict[str, dict[str, str]]:
            """Get all Traefik routes indexed by service name."""
            service_routes: dict[str, dict[str, str]] = {}

            for svc in services.values():
                routes = _get_traefik_routes(svc, traefik)
                if routes:
                    service_routes[svc.name] = routes

            return service_routes
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;services&#x22;" type="&#x22;dict[str, ServiceDefinition]&#x22;" value="null" />

        <PyParameter name="&#x22;traefik&#x22;" type="&#x22;TraefikContext | None&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, dict[str, str]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_get_service_ports&#x22;" type="&#x22;(service, env, running_containers, show_all, service_override=None, service_routes=None) -> list[PortMapping]&#x22;">
      Get port mappings for a service.

      <PySourceCode>
        ```python
        def _get_service_ports(
            service: ServiceDefinition,
            env: dict[str, str],
            running_containers: dict[str, Any],
            show_all: bool,
            service_override: dict[str, Any] | None = None,
            service_routes: dict[str, dict[str, str]] | None = None,
        ) -> list[PortMapping]:
            """Get port mappings for a service."""
            ports: list[PortMapping] = []
            compose_ports = service.compose.get("ports", [])
            if isinstance(service_override, dict) and service_override.get("ports"):
                compose_ports = service_override["ports"]

            if not compose_ports:
                return ports

            is_running = service.name in running_containers
            if not show_all and not is_running:
                return ports

            routes = service_routes.get(service.name, {}) if service_routes else {}

            for port_str in compose_ports:
                port_spec = _parse_compose_port_spec(port_str)
                container_port = int(port_spec.container_port)
                resolved_host_port, source, resolved_env_var = _resolve_host_port(
                    port_str=port_str,
                    port_spec=port_spec,
                    service_name=service.name,
                    container_port=container_port,
                    env=env,
                    running_containers=running_containers,
                )

                if resolved_host_port is None:
                    continue

                status = "Running" if is_running else "Stopped"

                url = routes.get(str(container_port))

                ports.append(
                    PortMapping(
                        service=service.name,
                        host_port=resolved_host_port,
                        container_port=container_port,
                        source=source,
                        status=status,
                        env_var=resolved_env_var,
                        url=url,
                    )
                )

            return ports
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;service&#x22;" type="&#x22;ServiceDefinition&#x22;" value="null" />

        <PyParameter name="&#x22;env&#x22;" type="&#x22;dict[str, str]&#x22;" value="null" />

        <PyParameter name="&#x22;running_containers&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />

        <PyParameter name="&#x22;show_all&#x22;" type="&#x22;bool&#x22;" value="null" />

        <PyParameter name="&#x22;service_override&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;service_routes&#x22;" type="&#x22;dict[str, dict[str, str]] | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.cli.commands.services.list[phlo.cli.commands.services.ports.PortMapping]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_detect_conflicts&#x22;" type="&#x22;(port_mappings) -> list[tuple[str, str, int]]&#x22;">
      Detect port conflicts. Returns list of (service1, service2, port) tuples.

      <PySourceCode>
        ```python
        def _detect_conflicts(port_mappings: list[PortMapping]) -> list[tuple[str, str, int]]:
            """Detect port conflicts. Returns list of (service1, service2, port) tuples."""
            host_port_to_services: dict[int, list[str]] = {}
            for pm in port_mappings:
                if pm.host_port not in host_port_to_services:
                    host_port_to_services[pm.host_port] = []
                if pm.service not in host_port_to_services[pm.host_port]:
                    host_port_to_services[pm.host_port].append(pm.service)

            conflicts = []
            for port, services in host_port_to_services.items():
                if len(services) > 1:
                    for i in range(len(services) - 1):
                        conflicts.append((services[i], services[i + 1], port))
            return conflicts
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;port_mappings&#x22;" type="&#x22;list[PortMapping]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.cli.commands.services.list[tuple[str, str, int]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_format_table&#x22;" type="&#x22;(port_mappings, conflicts) -> None&#x22;">
      Format and print the port table.

      <PySourceCode>
        ```python
        def _format_table(port_mappings: list[PortMapping], conflicts: list[tuple[str, str, int]]) -> None:
            """Format and print the port table."""
            if not port_mappings:
                click.echo("No port mappings found.")
                return

            conflict_ports = {c[2] for c in conflicts}

            has_urls = any(pm.url for pm in port_mappings)

            if has_urls:
                header = f"{'Service':<20} {'Host Port':<12} {'Container Port':<16} {'URL':<35} {'Source':<10} {'Status':<10}"
                separator = "-" * 105
            else:
                header = f"{'Service':<20} {'Host Port':<12} {'Container Port':<16} {'Source':<10} {'Status':<10}"
                separator = "-" * 70

            click.echo(header)
            click.echo(separator)

            for pm in sorted(port_mappings, key=lambda x: x.service):
                prefix = "⚠ " if pm.host_port in conflict_ports else "  "
                if has_urls:
                    url_str = pm.url or ""
                    row = (
                        f"{prefix}{pm.service:<18} "
                        f"{pm.host_port:<12} "
                        f"{pm.container_port:<16} "
                        f"{url_str:<35} "
                        f"{pm.source:<10} "
                        f"{pm.status:<10}"
                    )
                else:
                    row = (
                        f"{prefix}{pm.service:<18} "
                        f"{pm.host_port:<12} "
                        f"{pm.container_port:<16} "
                        f"{pm.source:<10} "
                        f"{pm.status:<10}"
                    )
                click.echo(row)

            if conflicts:
                click.echo("")
                for s1, s2, port in conflicts:
                    click.echo(f"⚠ Port conflict: {s1} and {s2} both map to host port {port}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;port_mappings&#x22;" type="&#x22;list[PortMapping]&#x22;" value="null" />

        <PyParameter name="&#x22;conflicts&#x22;" type="&#x22;list[tuple[str, str, int]]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_format_json&#x22;" type="&#x22;(port_mappings) -> None&#x22;">
      Format and print JSON output.

      <PySourceCode>
        ```python
        def _format_json(port_mappings: list[PortMapping]) -> None:
            """Format and print JSON output."""
            output = []
            for pm in port_mappings:
                output.append(
                    {
                        "service": pm.service,
                        "host_port": pm.host_port,
                        "container_port": pm.container_port,
                        "source": pm.source,
                        "status": pm.status.lower(),
                        "env_var": pm.env_var,
                        "url": pm.url,
                    }
                )
            click.echo(json.dumps(output, indent=2))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;port_mappings&#x22;" type="&#x22;list[PortMapping]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;ports_cmd&#x22;" type="&#x22;(output_json, show_all)&#x22;">
      Show port mappings for all services.

      Displays host port, container port, source (default/env/runtime), and status.

      <PySourceCode>
        ```python
        @click.command("ports")
        @click.option("--json", "output_json", is_flag=True, help="Output as JSON")
        @click.option("--all", "show_all", is_flag=True, help="Include stopped services with defaults")
        def ports_cmd(output_json: bool, show_all: bool):
            """Show port mappings for all services.

            Displays host port, container port, source (default/env/runtime), and status.

            Examples:
                phlo services ports
                phlo services ports --json
                phlo services ports --all
            """
            logger.info(
                "services_ports_requested",
                output_json=output_json,
                show_all=show_all,
            )

            phlo_dir = Path.cwd() / ".phlo"
            if not phlo_dir.exists():
                click.echo("Error: .phlo directory not found. Run 'phlo services init' first.", err=True)
                raise SystemExit(1)

            config_file = Path.cwd() / "phlo.yaml"
            existing_config: dict = {}
            if config_file.exists():
                try:
                    with config_file.open() as f:
                        existing_config = yaml.safe_load(f) or {}
                except (OSError, yaml.YAMLError) as exc:
                    logger.error("config_read_failed", exc_info=True)
                    raise click.ClickException(f"Failed to read {config_file}.") from exc

            _, disabled_services = get_enabled_disabled_service_names(existing_config)
            service_overrides = existing_config.get("services", {})

            env = _load_environment(phlo_dir, existing_config)

            try:
                discovery = ServiceDiscovery()
                available_services = discovery.discover()
            except Exception as exc:
                logger.error("services_discovery_failed", exc_info=True)
                raise click.ClickException(
                    "Failed to discover services. Verify service plugins are installed."
                ) from exc

            project_name = get_project_name()
            running_containers = _get_running_container_ports(project_name)

            traefik = _get_active_traefik_context(
                available_services,
                env,
                running_containers,
                disabled_services,
                service_overrides if isinstance(service_overrides, dict) else {},
            )
            service_routes = _get_service_routes(available_services, traefik)

            port_mappings: list[PortMapping] = []

            for svc in available_services.values():
                if svc.name in disabled_services:
                    continue
                service_override = (
                    service_overrides.get(svc.name, {}) if isinstance(service_overrides, dict) else {}
                )
                ports = _get_service_ports(
                    svc,
                    env,
                    running_containers,
                    show_all,
                    service_override=service_override if isinstance(service_override, dict) else None,
                    service_routes=service_routes,
                )
                port_mappings.extend(ports)

            conflicts = _detect_conflicts(port_mappings)

            if output_json:
                _format_json(port_mappings)
            else:
                _format_table(port_mappings, conflicts)

            logger.info(
                "services_ports_completed",
                total_mappings=len(port_mappings),
                conflicts=len(conflicts),
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;output_json&#x22;" type="&#x22;bool&#x22;" value="null" />

        <PyParameter name="&#x22;show_all&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>
</Tabs>
