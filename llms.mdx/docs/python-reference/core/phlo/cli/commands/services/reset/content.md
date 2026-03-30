# reset (/docs/python-reference/core/phlo/cli/commands/services/reset)



Reset command for resetting services and volumes.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;reset_cmd&#x22;" type="&#x22;(service, yes)&#x22;">
      Reset Phlo infrastructure by stopping services and deleting volumes.

      This stops all services and removes their data volumes for a clean slate.
      Use --service to selectively reset only specific service volumes.

      <PySourceCode>
        ```python
        @click.command("reset")
        @click.option(
            "--service",
            multiple=True,
            help="Reset only specific service(s) volumes (e.g., --service postgres,minio or --service postgres --service minio)",
        )
        @click.option(
            "--yes",
            "-y",
            is_flag=True,
            help="Skip confirmation prompt",
        )
        def reset_cmd(service: tuple[str, ...], yes: bool):
            """Reset Phlo infrastructure by stopping services and deleting volumes.

            This stops all services and removes their data volumes for a clean slate.
            Use --service to selectively reset only specific service volumes.

            Examples:
                phlo services reset                      # Reset everything
                phlo services reset --service postgres   # Reset only postgres
                phlo services reset --service postgres,minio  # Reset multiple
                phlo services reset -y                   # Skip confirmation
            """
            require_docker()
            phlo_dir = ensure_phlo_dir()
            compose_file = phlo_dir / "docker-compose.yml"
            project_name = get_project_name()
            volumes_dir = phlo_dir / "volumes"
            volumes_dir_resolved = volumes_dir.resolve()
            logger.info(
                "services_reset_requested",
                project_name=project_name,
                service_args_count=len(service),
                skip_confirmation=yes,
            )

            if not compose_file.exists():
                logger.error(
                    "services_reset_missing_compose_file",
                    project_name=project_name,
                    compose_file=str(compose_file),
                )
                click.echo("Error: docker-compose.yml not found.", err=True)
                click.echo("Run 'phlo services init' first.", err=True)
                sys.exit(1)

            # Parse comma-separated services
            services_list = []
            for s in service:
                services_list.extend(s.split(","))
            services_list = [s.strip() for s in services_list if s.strip()]

            # Determine what to reset
            def _resolve_volume_dir(service_name: str) -> Path:
                candidate = volumes_dir / service_name
                resolved = candidate.resolve()
                if not resolved.is_relative_to(volumes_dir_resolved):
                    raise ValueError(f"Invalid service path: {service_name}")
                return candidate

            if services_list:
                target = f"services: {', '.join(services_list)}"
                try:
                    volume_dirs = [_resolve_volume_dir(s) for s in services_list]
                except ValueError as exc:
                    logger.warning(
                        "services_reset_invalid_service_path",
                        project_name=project_name,
                        service_names=services_list,
                        error=str(exc),
                    )
                    click.echo(f"Error: {exc}", err=True)
                    sys.exit(1)
            else:
                target = "all services"
                volume_dirs = [volumes_dir] if volumes_dir.exists() else []

            # Confirm
            if not yes:
                click.echo(f"This will stop {target} and DELETE their data volumes.")
                if not click.confirm("Are you sure you want to continue?"):
                    logger.info(
                        "services_reset_aborted",
                        project_name=project_name,
                        target=target,
                    )
                    click.echo("Aborted.")
                    return

            # Stop services - selective or all
            if services_list:
                # Stop and remove only specific services
                click.echo(f"Stopping services: {', '.join(services_list)}...")
                cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
                cmd.extend(
                    [
                        "rm",
                        "-f",  # Force removal
                        "-s",  # Stop containers if running
                        "-v",  # Remove anonymous volumes
                        *services_list,  # Specific services
                    ]
                )
            else:
                # Stop all services
                click.echo(f"Stopping {project_name} infrastructure...")
                cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
                cmd.extend(
                    [
                        "down",
                        "-v",  # Remove Docker volumes
                    ]
                )
            logger.info(
                "services_reset_docker_started",
                project_name=project_name,
                target=target,
                service_count=len(services_list),
            )

            try:
                result = run_command(cmd, check=False, capture_output=False)
                if result.returncode != 0:
                    logger.warning(
                        "services_reset_docker_failed",
                        project_name=project_name,
                        returncode=result.returncode,
                        target=target,
                        service_count=len(services_list),
                    )
                    click.echo(
                        f"Warning: docker compose command failed with code {result.returncode}", err=True
                    )
                    click.echo(f"Command: {' '.join(cmd)}", err=True)
                else:
                    logger.info(
                        "services_reset_docker_completed",
                        project_name=project_name,
                        target=target,
                        service_count=len(services_list),
                    )
            except FileNotFoundError:
                logger.error("services_reset_docker_not_found", project_name=project_name, exc_info=True)
                click.echo("Error: docker command not found.", err=True)
                sys.exit(1)
            except TimeoutExpired:
                logger.warning(
                    "services_reset_docker_timeout",
                    project_name=project_name,
                    command=" ".join(cmd),
                    target=target,
                    exc_info=True,
                )
                click.echo("Warning: docker compose command timed out.", err=True)
                click.echo(f"Command: {' '.join(cmd)}", err=True)

            # Delete local volume directories
            deleted_count = 0
            for vol_dir in volume_dirs:
                if vol_dir.exists():
                    try:
                        resolved = vol_dir.resolve()
                        if not resolved.is_relative_to(volumes_dir_resolved):
                            click.echo(f"Warning: Skipping unsafe path {vol_dir}", err=True)
                            continue
                        if vol_dir.is_symlink():
                            click.echo(f"Warning: Skipping symlink {vol_dir}", err=True)
                            continue
                        if vol_dir.is_dir():
                            shutil.rmtree(vol_dir)
                            deleted_count += 1
                            click.echo(f"Deleted: {vol_dir.relative_to(phlo_dir)}")
                    except OSError as e:
                        logger.warning(
                            "services_reset_volume_delete_failed",
                            project_name=project_name,
                            volume_path=str(vol_dir),
                            error=str(e),
                        )
                        click.echo(f"Warning: Could not delete {vol_dir}: {e}", err=True)

            # Recreate volumes directory if we deleted it entirely
            if not services_list and not volumes_dir.exists():
                volumes_dir.mkdir(parents=True, exist_ok=True)
            logger.info(
                "services_reset_completed",
                project_name=project_name,
                target=target,
                deleted_count=deleted_count,
                service_count=len(services_list),
            )

            click.echo("")
            if services_list:
                click.echo(f"Reset complete for: {', '.join(services_list)}")
            else:
                click.echo("Full reset complete. All data volumes have been deleted.")
            click.echo("Run 'phlo services start' to start fresh.")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;service&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />

        <PyParameter name="&#x22;yes&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>
</Tabs>
