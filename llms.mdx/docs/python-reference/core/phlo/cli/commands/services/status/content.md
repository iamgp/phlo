# status (/docs/python-reference/core/phlo/cli/commands/services/status)



Status command for showing service status.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;status_cmd&#x22;" type="&#x22;()&#x22;">
      Show status of Phlo infrastructure services.

      <PySourceCode>
        ```python
        @click.command("status")
        def status_cmd():
            """Show status of Phlo infrastructure services.

            Examples:
                phlo services status
            """
            require_docker()
            phlo_dir = ensure_phlo_dir()
            project_name = get_project_name()
            logger.info(
                "services_status_requested",
                project_name=project_name,
                phlo_dir=str(phlo_dir),
            )

            cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
            cmd.extend(["ps", "--format", "table {{.Name}}\t{{.Status}}\t{{.Ports}}"])

            try:
                result = run_command(cmd, check=False, capture_output=False)
                if result.returncode != 0:
                    logger.warning(
                        "services_status_failed",
                        project_name=project_name,
                        returncode=result.returncode,
                    )
                    click.echo("No services running or error checking status.", err=True)
                    sys.exit(result.returncode or 1)
                logger.info("services_status_succeeded", project_name=project_name)
            except FileNotFoundError:
                logger.error(
                    "services_status_docker_not_found",
                    project_name=project_name,
                    exc_info=True,
                )
                click.echo("Error: docker command not found.", err=True)
                sys.exit(1)
            except TimeoutExpired:
                logger.error(
                    "services_status_timeout",
                    project_name=project_name,
                    command=" ".join(cmd),
                    exc_info=True,
                )
                click.echo("Error: docker compose timed out.", err=True)
                click.echo(f"Command: {' '.join(cmd)}", err=True)
                sys.exit(1)
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>
</Tabs>
