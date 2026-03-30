# logs (/docs/python-reference/core/phlo/cli/commands/services/logs)



Logs command for viewing service logs.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;logs_cmd&#x22;" type="&#x22;(service, follow, tail)&#x22;">
      View logs from Phlo infrastructure services.

      <PySourceCode>
        ```python
        @click.command("logs")
        @click.argument("service", required=False)
        @click.option("-f", "--follow", is_flag=True, help="Follow log output")
        @click.option("-n", "--tail", default=100, help="Number of lines to show")
        def logs_cmd(service: str | None, follow: bool, tail: int):
            """View logs from Phlo infrastructure services.

            Examples:
                phlo services logs
                phlo services logs dagster
                phlo services logs -f
            """
            require_docker()
            phlo_dir = ensure_phlo_dir()
            project_name = get_project_name()
            logger.info(
                "services_logs_requested",
                project_name=project_name,
                service_name=service,
                follow=follow,
                tail=tail,
            )

            cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
            cmd.extend(["logs", "--tail", str(tail)])

            if follow:
                cmd.append("-f")

            if service:
                cmd.append(service)

            try:
                result = run_command(cmd, check=False, capture_output=False)
                if result.returncode != 0:
                    logger.warning(
                        "services_logs_failed",
                        project_name=project_name,
                        service_name=service,
                        returncode=result.returncode,
                    )
                else:
                    logger.info(
                        "services_logs_completed",
                        project_name=project_name,
                        service_name=service,
                    )
            except FileNotFoundError:
                logger.error(
                    "services_logs_docker_not_found",
                    project_name=project_name,
                    service_name=service,
                    exc_info=True,
                )
                click.echo("Error: docker command not found.", err=True)
                sys.exit(1)
            except TimeoutExpired:
                logger.error(
                    "services_logs_timeout",
                    project_name=project_name,
                    service_name=service,
                    command=" ".join(cmd),
                    exc_info=True,
                )
                click.echo("Error: docker logs timed out.", err=True)
                click.echo(f"Command: {' '.join(cmd)}", err=True)
                sys.exit(1)
            except KeyboardInterrupt:
                logger.warning(
                    "services_logs_interrupted",
                    project_name=project_name,
                    service_name=service,
                )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;service&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;follow&#x22;" type="&#x22;bool&#x22;" value="null" />

        <PyParameter name="&#x22;tail&#x22;" type="&#x22;int&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>
</Tabs>
