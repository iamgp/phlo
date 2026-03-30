# restart (/docs/python-reference/core/phlo/cli/commands/services/restart)



Restart command for restarting services.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;restart_cmd&#x22;" type="&#x22;(build, profile, service, dev)&#x22;">
      Restart Phlo infrastructure services (stop + start).

      Combines stop and start in a single command for convenience.

      <PySourceCode>
        ```python
        @click.command("restart")
        @click.option("--build", is_flag=True, help="Build images before starting")
        @click.option(
            "--profile",
            multiple=True,
            help="Restart optional profile services (e.g., observability, api)",
        )
        @click.option(
            "--service",
            multiple=True,
            help="Restart only specific service(s) (e.g., --service postgres,minio)",
        )
        @click.option(
            "--dev",
            is_flag=True,
            help="Development mode: mount local phlo source for instant iteration",
        )
        def restart_cmd(
            build: bool,
            profile: tuple[str, ...],
            service: tuple[str, ...],
            dev: bool,
        ):
            """Restart Phlo infrastructure services (stop + start).

            Combines stop and start in a single command for convenience.

            Examples:
                phlo services restart                          # Restart all services
                phlo services restart --profile observability  # Restart profile services only
                phlo services restart --service postgres       # Restart specific service
                phlo services restart --build                  # Rebuild before starting
            """
            require_docker()
            if dev:
                logger.warning("services_restart_dev_mode_not_supported")
                raise click.UsageError("dev mode not implemented for restart")

            phlo_dir = ensure_phlo_dir()
            project_name = get_project_name()
            logger.info(
                "services_restart_requested",
                project_name=project_name,
                build=build,
                profile_count=len(profile),
            )

            # Parse comma-separated services
            services_list = []
            for s in service:
                services_list.extend(s.split(","))
            services_list = [s.strip() for s in services_list if s.strip()]

            # When --profile is specified without --service, target only profile services
            if profile and not services_list:
                services_list = get_profile_service_names(profile)
                if not services_list:
                    profile_list = ", ".join(profile)
                    logger.warning(
                        "services_restart_profile_resolved_empty",
                        project_name=project_name,
                        profiles=profile_list,
                    )
                    raise click.UsageError(f"profile(s) resolve to no services: {profile_list}")
            logger.info(
                "services_restart_targets_resolved",
                project_name=project_name,
                service_count=len(services_list),
                service_names=services_list,
            )

            if services_list:
                click.echo(f"Restarting services: {', '.join(services_list)}...")
            else:
                click.echo(f"Restarting {project_name} infrastructure...")

            # Stop services
            cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name, profiles=profile)
            if services_list:
                cmd.extend(["stop", *services_list])
            else:
                cmd.append("down")
            logger.info(
                "services_restart_stop_started",
                project_name=project_name,
                service_count=len(services_list),
                service_names=services_list,
            )

            try:
                result = run_command(cmd, check=False, capture_output=False)
                if result.returncode != 0:
                    logger.warning(
                        "services_restart_stop_failed",
                        project_name=project_name,
                        returncode=result.returncode,
                        service_count=len(services_list),
                        service_names=services_list,
                    )
                    click.echo(f"Warning: stop failed with code {result.returncode}", err=True)
                else:
                    logger.info(
                        "services_restart_stop_completed",
                        project_name=project_name,
                        service_count=len(services_list),
                        service_names=services_list,
                    )
            except FileNotFoundError:
                logger.error(
                    "services_restart_stop_docker_not_found",
                    project_name=project_name,
                    exc_info=True,
                )
                click.echo("Error: docker command not found.", err=True)
                sys.exit(1)
            except TimeoutExpired:
                logger.warning(
                    "services_restart_stop_timeout",
                    project_name=project_name,
                    service_count=len(services_list),
                    service_names=services_list,
                    exc_info=True,
                )
                click.echo("Warning: stop timed out.", err=True)

            # Start services
            click.echo("")
            cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name, profiles=profile)
            cmd.extend(["up", "-d"])

            if build:
                cmd.append("--build")

            if services_list:
                cmd.extend(services_list)
            logger.info(
                "services_restart_start_started",
                project_name=project_name,
                service_count=len(services_list),
                service_names=services_list,
                build=build,
            )

            try:
                result = run_command(cmd, check=False, capture_output=False)
                if result.returncode == 0:
                    logger.info(
                        "services_restart_succeeded",
                        project_name=project_name,
                        service_count=len(services_list),
                        service_names=services_list,
                        build=build,
                    )
                    click.echo("")
                    if services_list:
                        click.echo(f"Restarted services: {', '.join(services_list)}")
                    else:
                        click.echo(f"{project_name} infrastructure restarted.")
                else:
                    logger.error(
                        "services_restart_start_failed",
                        project_name=project_name,
                        returncode=result.returncode,
                        service_count=len(services_list),
                        service_names=services_list,
                    )
                    click.echo(f"Error: start failed with code {result.returncode}", err=True)
                    click.echo(f"Command: {' '.join(cmd)}", err=True)
                    sys.exit(result.returncode)
            except FileNotFoundError:
                logger.error(
                    "services_restart_start_docker_not_found",
                    project_name=project_name,
                    exc_info=True,
                )
                click.echo("Error: docker command not found.", err=True)
                sys.exit(1)
            except TimeoutExpired:
                logger.error(
                    "services_restart_start_timeout",
                    project_name=project_name,
                    command=" ".join(cmd),
                    service_count=len(services_list),
                    service_names=services_list,
                    exc_info=True,
                )
                click.echo("Error: docker compose timed out.", err=True)
                click.echo(f"Command: {' '.join(cmd)}", err=True)
                sys.exit(1)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;build&#x22;" type="&#x22;bool&#x22;" value="null" />

        <PyParameter name="&#x22;profile&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />

        <PyParameter name="&#x22;service&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />

        <PyParameter name="&#x22;dev&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>
</Tabs>
