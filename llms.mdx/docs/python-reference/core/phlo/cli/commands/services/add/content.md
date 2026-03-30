# add (/docs/python-reference/core/phlo/cli/commands/services/add)



Add command for rendering optional services into the project stack.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_load_project_config&#x22;" type="&#x22;(config_file) -> dict&#x22;">
      Load project config, ensuring a mapping root.

      <PySourceCode>
        ```python
        def _load_project_config(config_file: Path) -> dict:
            """Load project config, ensuring a mapping root."""
            if config_file.exists():
                with config_file.open() as handle:
                    config = yaml.safe_load(handle) or {}
                if not isinstance(config, dict):
                    logger.error("services_add_invalid_config_mapping", config_file=str(config_file))
                    click.echo("Error: phlo.yaml must contain a mapping.", err=True)
                    sys.exit(1)
                return config

            logger.error("services_add_missing_config", config_file=str(config_file))
            click.echo("Error: phlo.yaml not found.", err=True)
            sys.exit(1)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;config_file&#x22;" type="&#x22;Path&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_validate_profiles&#x22;" type="&#x22;(discovery, profile_names) -> tuple[str, ...]&#x22;">
      Normalize and validate requested profile names.

      <PySourceCode>
        ```python
        def _validate_profiles(
            discovery: ServiceDiscovery, profile_names: tuple[str, ...]
        ) -> tuple[str, ...]:
            """Normalize and validate requested profile names."""
            requested_profiles = tuple(
                dict.fromkeys(name.strip() for name in profile_names if name.strip())
            )
            if not requested_profiles:
                return ()

            available_profiles = discovery.get_available_profiles()
            unknown_profiles = sorted(set(requested_profiles) - available_profiles)
            if unknown_profiles:
                click.echo(
                    f"Error: Unknown profile(s): {', '.join(unknown_profiles)}. "
                    f"Available profiles: {', '.join(sorted(available_profiles)) or '(none)'}",
                    err=True,
                )
                sys.exit(1)
            return requested_profiles
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;discovery&#x22;" type="&#x22;ServiceDiscovery&#x22;" value="null" />

        <PyParameter name="&#x22;profile_names&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;tuple[str, ...]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_normalize_service_names&#x22;" type="&#x22;(service_names) -> list[str]&#x22;">
      Normalize repeated/comma-separated service arguments.

      <PySourceCode>
        ```python
        def _normalize_service_names(service_names: tuple[str, ...]) -> list[str]:
            """Normalize repeated/comma-separated service arguments."""
            normalized: list[str] = []
            for item in service_names:
                normalized.extend(name.strip() for name in item.split(",") if name.strip())
            return list(dict.fromkeys(normalized))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;service_names&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.cli.commands.services.list[str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_update_config_enabled_services&#x22;" type="&#x22;(config, *, services_to_enable) -> tuple[list[str], list[str]]&#x22;">
      Persist enabled/disabled service state into phlo.yaml.

      <PySourceCode>
        ```python
        def _update_config_enabled_services(
            config: dict,
            *,
            services_to_enable: list[str],
        ) -> tuple[list[str], list[str]]:
            """Persist enabled/disabled service state into phlo.yaml."""
            enabled_names, disabled_names = normalize_services_enabled_disabled_config(config)
            enabled_set = set(enabled_names)
            disabled_set = set(disabled_names)

            for service_name in services_to_enable:
                enabled_set.add(service_name)
                disabled_set.discard(service_name)

            services_config = config.setdefault("services", {})
            if not isinstance(services_config, dict):
                services_config = {}
                config["services"] = services_config

            services_config["enabled"] = sorted(enabled_set)
            services_config["disabled"] = sorted(disabled_set)
            return services_config["enabled"], services_config["disabled"]
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;config&#x22;" type="&#x22;dict&#x22;" value="null" />

        <PyParameter name="&#x22;services_to_enable&#x22;" type="&#x22;list[str]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;tuple[phlo.cli.commands.services.list[str], phlo.cli.commands.services.list[str]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_start_services&#x22;" type="&#x22;(*, phlo_dir, project_name, profile_names, service_names) -> None&#x22;">
      Start newly-added services.

      <PySourceCode>
        ```python
        def _start_services(
            *,
            phlo_dir: Path,
            project_name: str,
            profile_names: tuple[str, ...],
            service_names: list[str],
        ) -> None:
            """Start newly-added services."""
            cmd = compose_base_cmd(
                phlo_dir=phlo_dir,
                project_name=project_name,
                profiles=profile_names,
            )
            cmd.extend(["up", "-d", *service_names])
            try:
                result = run_command(cmd, check=False, capture_output=False)
            except (FileNotFoundError, TimeoutExpired, OSError) as exc:
                logger.error(
                    "services_add_start_exception",
                    project_name=project_name,
                    profile_count=len(profile_names),
                    service_count=len(service_names),
                    error_type=type(exc).__name__,
                    exc_info=True,
                )
                click.echo(f"Warning: Could not start services: {exc}", err=True)
                click.echo(f"Command: {' '.join(cmd)}", err=True)
                return

            if result.returncode != 0:
                logger.warning(
                    "services_add_start_failed",
                    project_name=project_name,
                    profile_count=len(profile_names),
                    service_count=len(service_names),
                    returncode=result.returncode,
                )
                click.echo("Warning: Could not start requested services.", err=True)
                click.echo(f"Command: {' '.join(cmd)}", err=True)
                return

            logger.info(
                "services_add_start_succeeded",
                project_name=project_name,
                profile_count=len(profile_names),
                service_count=len(service_names),
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;phlo_dir&#x22;" type="&#x22;Path&#x22;" value="null" />

        <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;profile_names&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />

        <PyParameter name="&#x22;service_names&#x22;" type="&#x22;list[str]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;add_cmd&#x22;" type="&#x22;(service_name, profiles, services, no_start) -> None&#x22;">
      Add optional services or profiles to the rendered project stack.

      <PySourceCode>
        ```python
        @click.command("add")
        @click.argument("service_name", required=False)
        @click.option(
            "--profile",
            "profiles",
            multiple=True,
            help="Render all services from an optional profile (e.g., --profile api)",
        )
        @click.option(
            "--service",
            "services",
            multiple=True,
            help="Render explicit service(s) (e.g., --service superset --service phlo-api)",
        )
        @click.option("--no-start", is_flag=True, help="Don't start newly-added services after rendering")
        def add_cmd(
            service_name: str | None,
            profiles: tuple[str, ...],
            services: tuple[str, ...],
            no_start: bool,
        ) -> None:
            """Add optional services or profiles to the rendered project stack.

            Examples:
                phlo services add phlo-api
                phlo services add --profile api
                phlo services add --profile proxy --service superset
                phlo services add --service hasura --service postgrest --no-start
            """
            phlo_dir = get_phlo_dir()
            config_file = Path.cwd() / PHLO_CONFIG_FILE
            logger.info(
                "services_add_requested",
                positional_service=service_name,
                profile_count=len(profiles),
                explicit_service_arg_count=len(services),
                no_start=no_start,
            )

            if not phlo_dir.exists():
                logger.error("services_add_missing_phlo_dir", phlo_dir=str(phlo_dir))
                click.echo("Error: .phlo directory not found.", err=True)
                click.echo("Run 'phlo services init' first.", err=True)
                sys.exit(1)

            config = _load_project_config(config_file)
            discovery = ServiceDiscovery()
            all_services = discovery.discover()

            normalized_profiles = _validate_profiles(discovery, profiles)
            explicit_services = _normalize_service_names(services)
            if service_name:
                explicit_services = [service_name, *explicit_services]
                explicit_services = list(dict.fromkeys(explicit_services))

            if not normalized_profiles and not explicit_services:
                click.echo("Error: Specify a service name, --service, or --profile.", err=True)
                sys.exit(1)

            unknown_services = [name for name in explicit_services if name not in all_services]
            if unknown_services:
                click.echo(f"Error: Unknown service name(s): {', '.join(unknown_services)}", err=True)
                sys.exit(1)

            profile_services = get_profile_service_names(normalized_profiles)
            services_to_enable = list(dict.fromkeys([*profile_services, *explicit_services]))

            if not services_to_enable:
                click.echo("Nothing to add.", err=True)
                sys.exit(1)

            _update_config_enabled_services(config, services_to_enable=services_to_enable)

            with config_file.open("w") as handle:
                yaml.dump(config, handle, default_flow_style=False, sort_keys=False)

            logger.info(
                "services_add_config_updated",
                service_count=len(services_to_enable),
                profile_count=len(normalized_profiles),
            )
            click.echo(f"Updated: {PHLO_CONFIG_FILE}")

            _regenerate_compose(discovery, config, phlo_dir)

            if normalized_profiles:
                click.echo(f"Added profiles: {', '.join(normalized_profiles)}")
            if explicit_services:
                click.echo(f"Added services: {', '.join(explicit_services)}")

            if no_start:
                return

            click.echo("")
            click.echo("Starting newly-added services...")
            _start_services(
                phlo_dir=phlo_dir,
                project_name=get_project_name(),
                profile_names=normalized_profiles,
                service_names=services_to_enable,
            )
            click.echo("Services added and started.")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;profiles&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />

        <PyParameter name="&#x22;services&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />

        <PyParameter name="&#x22;no_start&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
