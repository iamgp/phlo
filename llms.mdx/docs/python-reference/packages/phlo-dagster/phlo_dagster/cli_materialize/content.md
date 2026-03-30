# cli_materialize (/docs/python-reference/packages/phlo-dagster/phlo_dagster/cli_materialize)



Materialize command for Dagster assets via Docker.

This module implements the `phlo materialize` CLI command, providing a
convenient interface for materializing Dagster assets through Docker
container execution. It handles environment setup and passes through
to Dagster's asset materialization CLI.

Features:

* Single asset or asset selection expression materialization
* Partition support for time-sliced assets
* Schema contract refresh control
* Dry-run mode for command preview
* Platform-aware environment injection (PHLO\_HOST\_PLATFORM)
* Automatic Dagster container discovery
* Streaming output from container execution

Environment Variables:

* PHLO\_HOST\_PLATFORM: Host OS platform for DuckDB compatibility
* PHLO\_PROJECT\_PATH: Project path within container
* PHLO\_AUTO\_REFRESH\_CONTRACTS: Enable schema contract refresh
* PHLO\_CONTRACT\_REFRESH\_SELECTION: Assets to refresh contracts for

Docker Integration:
The command uses `docker exec` to run Dagster CLI commands within
the running Dagster container. This ensures:

* Access to configured resources (Trino, MinIO, etc.)
* Consistent Python environment
* Proper logging context

Example:
CLI usage::

phlo materialize dlt\_orders
phlo materialize dlt\_orders --partition 2025-01-15
phlo materialize --select "tag:bronze"
phlo materialize dlt\_orders --dry-run
phlo materialize dlt\_orders --no-contract-refresh

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;materialize&#x22;" type="&#x22;(asset_name, partition, select, no_contract_refresh, dry_run) -> None&#x22;">
      Materialize Dagster assets via Docker.

      <PySourceCode>
        ```python
        @click.command()
        @click.argument("asset_name")
        @click.option("-p", "--partition", help="Partition date (YYYY-MM-DD)")
        @click.option("--select", help="Asset selector expression")
        @click.option(
            "--no-contract-refresh",
            is_flag=True,
            help="Skip automatic schema contract refresh before materialization",
        )
        @click.option("--dry-run", is_flag=True, help="Show command without executing")
        def materialize(
            asset_name: str,
            partition: Optional[str],
            select: Optional[str],
            no_contract_refresh: bool,
            dry_run: bool,
        ) -> None:
            """Materialize Dagster assets via Docker.

            Args:
                asset_name: Name of the asset to materialize.
                partition: Optional partition date (YYYY-MM-DD) for partitioned assets.
                select: Optional asset selector expression to override asset_name.
                no_contract_refresh: If True, skip automatic schema contract refresh.
                dry_run: If True, show command without executing.

            Returns:
                None

            Raises:
                SystemExit: On command failure or Docker not found.

            """
            logger = get_logger("phlo.dagster.materialize", service="dagster")
            started_at = time.perf_counter()
            project_name = get_project_name()
            container_name = "dagster"
            logger.info(
                "dagster_materialize_command_started",
                asset_name=asset_name,
                partition=partition,
                select=select,
                no_contract_refresh=no_contract_refresh,
                dry_run=dry_run,
                project_name=project_name,
            )

            try:
                container_name = find_dagster_container(project_name)
                host_platform = platform.system()

                cmd = [
                    "docker",
                    "exec",
                    "-e",
                    f"PHLO_HOST_PLATFORM={host_platform}",
                    "-e",
                    "PHLO_PROJECT_PATH=/app",
                    "-e",
                    f"PHLO_AUTO_REFRESH_CONTRACTS={'0' if no_contract_refresh else '1'}",
                    "-e",
                    f"PHLO_CONTRACT_REFRESH_SELECTION={select or asset_name}",
                    "-w",
                    "/app",
                    container_name,
                    "dagster",
                    "asset",
                    "materialize",
                    "-m",
                    "phlo_dagster.framework.definitions",
                ]

                if select:
                    cmd.extend(["--select", select])
                else:
                    cmd.extend(["--select", asset_name])

                if partition:
                    cmd.extend(["--partition", partition])

                if dry_run:
                    click.echo("Dry run - would execute:\n")
                    click.echo(" ".join(cmd))
                    logger.info(
                        "dagster_materialize_command_completed",
                        asset_name=asset_name,
                        partition=partition,
                        select=select,
                        no_contract_refresh=no_contract_refresh,
                        dry_run=True,
                        project_name=project_name,
                        container_name=container_name,
                        duration_seconds=round(time.perf_counter() - started_at, 3),
                        returncode=0,
                    )
                    sys.exit(0)

                click.echo(f"Materializing {asset_name}...\n")

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                if process.stdout:
                    for line in process.stdout:
                        sys.stdout.write(line)
                        sys.stdout.flush()
                        message = line.rstrip()
                        if message:
                            logger.info(message, tags={"source": "dagster"})
                returncode = process.wait()
                if returncode == 0:
                    click.echo(f"\nSuccessfully materialized {asset_name}")
                    logger.info(
                        "dagster_materialize_command_completed",
                        asset_name=asset_name,
                        partition=partition,
                        select=select,
                        no_contract_refresh=no_contract_refresh,
                        dry_run=False,
                        project_name=project_name,
                        container_name=container_name,
                        duration_seconds=round(time.perf_counter() - started_at, 3),
                        returncode=returncode,
                    )
                else:
                    click.echo(
                        f"\nMaterialization failed with exit code {returncode}",
                        err=True,
                    )
                    logger.error(
                        "dagster_materialize_command_failed",
                        asset_name=asset_name,
                        partition=partition,
                        select=select,
                        no_contract_refresh=no_contract_refresh,
                        dry_run=False,
                        project_name=project_name,
                        container_name=container_name,
                        duration_seconds=round(time.perf_counter() - started_at, 3),
                        returncode=returncode,
                    )
                sys.exit(returncode)
            except FileNotFoundError:
                logger.error(
                    "dagster_materialize_command_failed",
                    asset_name=asset_name,
                    partition=partition,
                    select=select,
                    no_contract_refresh=no_contract_refresh,
                    dry_run=dry_run,
                    project_name=project_name,
                    duration_seconds=round(time.perf_counter() - started_at, 3),
                    error="docker_not_found_or_container_not_running",
                    exc_info=True,
                )
                click.echo(
                    f"Error: Docker not found or {container_name} container not running",
                    err=True,
                )
                click.echo("\nStart services with: phlo services start", err=True)
                sys.exit(1)
            except Exception as exc:
                logger.error(
                    "dagster_materialize_command_failed",
                    asset_name=asset_name,
                    partition=partition,
                    select=select,
                    no_contract_refresh=no_contract_refresh,
                    dry_run=dry_run,
                    project_name=project_name,
                    duration_seconds=round(time.perf_counter() - started_at, 3),
                    error=str(exc),
                    exc_info=True,
                )
                raise
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Name of the asset to materialize.
        </PyParameter>

        <PyParameter name="&#x22;partition&#x22;" type="&#x22;Optional[str]&#x22;" value="undefined">
          Optional partition date (YYYY-MM-DD) for partitioned assets.
        </PyParameter>

        <PyParameter name="&#x22;select&#x22;" type="&#x22;Optional[str]&#x22;" value="undefined">
          Optional asset selector expression to override asset\_name.
        </PyParameter>

        <PyParameter name="&#x22;no_contract_refresh&#x22;" type="&#x22;bool&#x22;" value="undefined">
          If True, skip automatic schema contract refresh.
        </PyParameter>

        <PyParameter name="&#x22;dry_run&#x22;" type="&#x22;bool&#x22;" value="undefined">
          If True, show command without executing.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;">
        None
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
