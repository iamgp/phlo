# cli (/docs/python-reference/packages/phlo-minio/phlo_minio/cli)



CLI commands for MinIO S3-compatible object storage operations.

This module provides Click-based CLI commands for interacting with MinIO,
including listing buckets/objects and retrieving admin information. All
commands execute inside the MinIO Docker container using the mc (MinIO Client).

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_require_docker&#x22;" type="&#x22;() -> None&#x22;">
      Validate that Docker CLI is installed and available.

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        Uses shutil.which to check for docker executable in system PATH.
      </Callout>

      <PySourceCode>
        ```python
        def _require_docker() -> None:
            """Validate that Docker CLI is installed and available.

            Raises:
                click.ClickException: If the docker command is not found in PATH.

            Examples:
                Validation check:
                    >>> _require_docker()  # Raises if docker not found

                Integration in commands:
                    @click.command()
                    def my_command():
                        _require_docker()  # Ensure docker before proceeding
                        # ... command logic

            Note:
                Uses shutil.which to check for docker executable in system PATH.

            """
            if which("docker") is None:
                raise click.ClickException("docker command not found.")
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_mc_exec_base&#x22;" type="&#x22;(*, tty) -> list[str]&#x22;">
      Build the docker compose exec command base for MinIO client operations.

      Constructs a command list that will execute mc (MinIO Client) commands
      inside the running MinIO container via docker compose exec.

      <Callout title="&#x22;Implementation&#x22;" type="&#x22;implementation&#x22;">
        Uses phlo CLI infrastructure to determine project configuration:

        * ensure\_phlo\_dir: Locate .phlo directory
        * get\_project\_name: Get compose project name
        * compose\_base\_cmd: Build base docker compose command
      </Callout>

      <PySourceCode>
        ```python
        def _mc_exec_base(*, tty: bool) -> list[str]:
            """Build the docker compose exec command base for MinIO client operations.

            Constructs a command list that will execute mc (MinIO Client) commands
            inside the running MinIO container via docker compose exec.

            Args:
                tty: Whether to allocate a TTY. Set True for interactive commands,
                    False for programmatic output capture.

            Returns:
                list[str]: Command list starting with docker compose exec,
                    ending with "minio", "mc" ready for subcommand arguments.

            Examples:
                Non-TTY for programmatic use:
                    >>> cmd = _mc_exec_base(tty=False)
                    >>> cmd.extend(["ls", "local/my-bucket"])
                    # Result: ['docker', 'compose', ..., 'exec', '-T', 'minio', 'mc', 'ls', ...]

                TTY for interactive use:
                    >>> cmd = _mc_exec_base(tty=True)
                    >>> cmd.extend(["admin", "info"])
                    # Result: ['docker', 'compose', ..., 'exec', 'minio', 'mc', 'admin', 'info']

            Implementation:
                Uses phlo CLI infrastructure to determine project configuration:
                    - ensure_phlo_dir: Locate .phlo directory
                    - get_project_name: Get compose project name
                    - compose_base_cmd: Build base docker compose command

            """
            phlo_dir = ensure_phlo_dir()
            project_name = get_project_name()
            cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
            cmd.append("exec")
            if not tty:
                cmd.append("-T")
            cmd.extend(["minio", "mc"])
            return cmd
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;tty&#x22;" type="&#x22;bool&#x22;" value="undefined">
          Whether to allocate a TTY. Set True for interactive commands,
          False for programmatic output capture.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        list\[str]: Command list starting with docker compose exec,
        ending with "minio", "mc" ready for subcommand arguments.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;minio_group&#x22;" type="&#x22;(ctx, mc_args) -> None&#x22;">
      Run MinIO client (mc) commands inside the project service container.

      This is the main entry point for MinIO CLI operations. It handles
      common subcommands like 'ls' and 'admin info' with dedicated handlers,
      while passing other commands directly to the mc binary.

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        The 'ls' and 'admin info' subcommands have dedicated handlers
        for better output formatting. All other commands are passed
        directly to mc inside the MinIO container.
      </Callout>

      <PySourceCode>
        ```python
        @click.command(
            name="minio",
            context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
        )
        @click.argument("mc_args", nargs=-1, type=click.UNPROCESSED)
        @click.pass_context
        def minio_group(ctx: click.Context, mc_args: tuple[str, ...]) -> None:
            """Run MinIO client (mc) commands inside the project service container.

            This is the main entry point for MinIO CLI operations. It handles
            common subcommands like 'ls' and 'admin info' with dedicated handlers,
            while passing other commands directly to the mc binary.

            Args:
                ctx: Click context object.
                mc_args: Variable arguments passed to mc command.

            Raises:
                click.ClickException: If the mc command exits with non-zero status.

            Examples:
                List all buckets:
                    $ phlo minio ls
                    [2024-01-15 10:30:00 UTC]     0B my-bucket/

                List with recursion:
                    $ phlo minio ls local/my-bucket --recursive

                Direct mc commands:
                    $ phlo minio mb local/new-bucket  # Make bucket
                    $ phlo minio cp file.txt local/my-bucket/  # Copy file
                    $ phlo minio mirror local/data/ local/my-bucket/  # Mirror directory

                Admin operations:
                    $ phlo minio admin info
                    $ phlo minio admin info --json

                Alias configuration:
                    $ phlo minio alias set myminio http://localhost:10001 minio minio123

            Note:
                The 'ls' and 'admin info' subcommands have dedicated handlers
                for better output formatting. All other commands are passed
                directly to mc inside the MinIO container.

            """
            if mc_args and mc_args[0] == "ls":
                minio_ls.main(
                    args=list(mc_args[1:]),
                    prog_name="phlo minio ls",
                    standalone_mode=False,
                )
                return
            if len(mc_args) >= 2 and mc_args[0] == "admin" and mc_args[1] == "info":
                minio_admin_info.main(
                    args=list(mc_args[2:]),
                    prog_name="phlo minio admin info",
                    standalone_mode=False,
                )
                return

            _require_docker()
            cmd = _mc_exec_base(tty=True)
            cmd.extend(mc_args)
            result = subprocess.run(cmd, check=False)
            if result.returncode != 0:
                raise click.ClickException(f"mc exited with status {result.returncode}.")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;ctx&#x22;" type="&#x22;click.Context&#x22;" value="undefined">
          Click context object.
        </PyParameter>

        <PyParameter name="&#x22;mc_args&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="undefined">
          Variable arguments passed to mc command.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;minio_ls&#x22;" type="&#x22;(target, recursive, as_json, timeout_seconds) -> None&#x22;">
      List objects or buckets using the MinIO client.

      Lists S3 buckets or objects within a bucket using the mc ls command.
      Supports recursive listing and JSON output for programmatic use.

      <Callout title="&#x22;Use Case&#x22;" type="&#x22;use-case&#x22;">
        Verify data lake contents:
        $ phlo minio ls local/raw-data/invoices/ --recursive --json |                 jq 'select(.size > 1000000) | .key'

        List all files larger than 1MB [#list-all-files-larger-than-1mb]
      </Callout>

      <PySourceCode>
        ```python
        @click.command(name="ls")
        @click.argument("target", default="local/")
        @click.option("--recursive", is_flag=True, help="List recursively.")
        @click.option("--json", "as_json", is_flag=True, help="Emit JSON lines from mc.")
        @click.option("--timeout", "timeout_seconds", default=30, show_default=True, type=int)
        def minio_ls(target: str, recursive: bool, as_json: bool, timeout_seconds: int) -> None:
            """List objects or buckets using the MinIO client.

            Lists S3 buckets or objects within a bucket using the mc ls command.
            Supports recursive listing and JSON output for programmatic use.

            Args:
                target: Target path to list (default: "local/" for all buckets).
                    Format: alias/bucket/path (e.g., "local/my-bucket/data/").
                recursive: If True, list all objects recursively.
                as_json: If True, output JSON lines instead of formatted text.
                timeout_seconds: Command timeout in seconds.

            Raises:
                click.ClickException: If command fails or times out.

            Examples:
                List all buckets:
                    $ phlo minio ls
                    [2024-01-15 10:30:00 UTC]     0B my-bucket/
                    [2024-01-15 10:30:00 UTC]     0B staging-bucket/

                List bucket contents:
                    $ phlo minio ls local/my-bucket
                    [2024-01-15 10:30:00 UTC]  1.5MiB data/
                    [2024-01-15 10:30:00 UTC]  256KiB config.yaml

                Recursive listing:
                    $ phlo minio ls local/my-bucket --recursive
                    [2024-01-15 10:30:00 UTC]  1.5MiB data/partition1/
                    [2024-01-15 10:30:00 UTC]  256KiB data/partition1/file.parquet
                    ...

                JSON output for scripts:
                    $ phlo minio ls local/my-bucket --json | jq '.key'
                    "data/partition1/file.parquet"
                    "data/partition2/file.parquet"

                List with custom timeout:
                    $ phlo minio ls local/large-bucket --recursive --timeout 120

            Use Case:
                Verify data lake contents:
                    $ phlo minio ls local/raw-data/invoices/ --recursive --json | \
                        jq 'select(.size > 1000000) | .key'
                    # List all files larger than 1MB

            """
            _require_docker()
            cmd = _mc_exec_base(tty=False)
            cmd.append("ls")
            if recursive:
                cmd.append("--recursive")
            if as_json:
                cmd.append("--json")
            cmd.append(target)

            try:
                result = run_command(
                    cmd,
                    timeout_seconds=timeout_seconds,
                    capture_output=True,
                    check=True,
                )
            except CommandError as exc:
                stderr = exc.stderr.strip()
                raise click.ClickException(stderr or str(exc)) from exc
            except TimeoutExpired as exc:
                raise click.ClickException(f"List timed out after {timeout_seconds} seconds.") from exc

            if result.stdout:
                click.echo(result.stdout, nl=False)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="undefined">
          Target path to list (default: "local/" for all buckets).
          Format: alias/bucket/path (e.g., "local/my-bucket/data/").
        </PyParameter>

        <PyParameter name="&#x22;recursive&#x22;" type="&#x22;bool&#x22;" value="undefined">
          If True, list all objects recursively.
        </PyParameter>

        <PyParameter name="&#x22;as_json&#x22;" type="&#x22;bool&#x22;" value="undefined">
          If True, output JSON lines instead of formatted text.
        </PyParameter>

        <PyParameter name="&#x22;timeout_seconds&#x22;" type="&#x22;int&#x22;" value="undefined">
          Command timeout in seconds.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;minio_admin_info&#x22;" type="&#x22;(target, as_json, timeout_seconds) -> None&#x22;">
      Show MinIO server admin information.

      Retrieves administrative information about the MinIO server
      using the mc admin info command. Useful for monitoring server
      health, storage usage, and cluster status.

      <Callout title="&#x22;Use Case&#x22;" type="&#x22;use-case&#x22;">
        Health check in CI/CD:
        $ phlo minio admin info --json | jq -e '.status == "success"' > /dev/null

        Exit code indicates server health status [#exit-code-indicates-server-health-status]
      </Callout>

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        Requires admin privileges on the MinIO server.
      </Callout>

      <PySourceCode>
        ```python
        @click.command(name="info")
        @click.argument("target", default="local/")
        @click.option("--json", "as_json", is_flag=True, help="Emit JSON output from mc.")
        @click.option("--timeout", "timeout_seconds", default=30, show_default=True, type=int)
        def minio_admin_info(target: str, as_json: bool, timeout_seconds: int) -> None:
            """Show MinIO server admin information.

            Retrieves administrative information about the MinIO server
            using the mc admin info command. Useful for monitoring server
            health, storage usage, and cluster status.

            Args:
                target: Target MinIO alias (default: "local/").
                as_json: If True, output JSON instead of formatted text.
                timeout_seconds: Command timeout in seconds.

            Raises:
                click.ClickException: If command fails or times out.

            Examples:
                Basic server info:
                    $ phlo minio admin info
                    ●  minio:10001
                       Uptime: 3 hours 45 minutes
                       Version: 2024-01-15T20:30:00Z
                       Network: 1/1 OK
                       Drives: 1/1 OK

                JSON output for monitoring:
                    $ phlo minio admin info --json | jq '.info.servers[0]'
                    {
                      "state": "online",
                      "endpoint": "minio:10001",
                      "uptime": 13500000000000,
                      ...
                    }

                Check specific alias:
                    $ phlo minio admin info mycustom/

            Use Case:
                Health check in CI/CD:
                    $ phlo minio admin info --json | jq -e '.status == "success"' > /dev/null
                    # Exit code indicates server health status

            Note:
                Requires admin privileges on the MinIO server.

            """
            _require_docker()
            cmd = _mc_exec_base(tty=False)
            cmd.extend(["admin", "info"])
            if as_json:
                cmd.append("--json")
            cmd.append(target)

            try:
                result = run_command(
                    cmd,
                    timeout_seconds=timeout_seconds,
                    capture_output=True,
                    check=True,
                )
            except CommandError as exc:
                stderr = exc.stderr.strip()
                raise click.ClickException(stderr or str(exc)) from exc
            except TimeoutExpired as exc:
                raise click.ClickException(
                    f"Admin info timed out after {timeout_seconds} seconds."
                ) from exc

            if result.stdout:
                click.echo(result.stdout, nl=False)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="undefined">
          Target MinIO alias (default: "local/").
        </PyParameter>

        <PyParameter name="&#x22;as_json&#x22;" type="&#x22;bool&#x22;" value="undefined">
          If True, output JSON instead of formatted text.
        </PyParameter>

        <PyParameter name="&#x22;timeout_seconds&#x22;" type="&#x22;int&#x22;" value="undefined">
          Command timeout in seconds.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
