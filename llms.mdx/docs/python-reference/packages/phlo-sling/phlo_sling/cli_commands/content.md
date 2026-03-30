# cli_commands (/docs/python-reference/packages/phlo-sling/phlo_sling/cli_commands)



CLI commands for Sling replication management.

This module implements the Click command-line interface for Sling replication
operations. It provides commands for running ad-hoc replications, listing
available connections, and discovering source streams from connections.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;sling_group&#x22;" type="&#x22;() -> None&#x22;">
      Sling replication commands.

      This command group provides operations for managing Sling-based data
      replications within the Phlo platform. Commands include running
      replications, listing connections, and discovering source streams.

      <PySourceCode>
        ```python
        @click.group("sling")
        def sling_group() -> None:
            """Sling replication commands.

            This command group provides operations for managing Sling-based data
            replications within the Phlo platform. Commands include running
            replications, listing connections, and discovering source streams.
            """
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;run_command&#x22;" type="&#x22;(replication, source, target, stream, target_object, mode) -> None&#x22;">
      Run a Sling replication.

      Execute a data replication using Sling. Either provide a replication
      YAML configuration file or specify source/target/stream parameters
      for ad-hoc execution.

      <PySourceCode>
        ```python
        @sling_group.command("run")
        @click.option("--replication", "-r", type=click.Path(exists=True), help="Sling replication YAML.")
        @click.option("--source", "-s", help="Source connection name.")
        @click.option("--target", "-t", help="Target connection name.")
        @click.option("--stream", help="Source stream (e.g., 'public.users').")
        @click.option("--object", "target_object", help="Target object/table name.")
        @click.option(
            "--mode",
            default=None,
            help="Replication mode. Defaults to SLING_DEFAULT_MODE when omitted.",
        )
        def run_command(
            replication: str | None,
            source: str | None,
            target: str | None,
            stream: str | None,
            target_object: str | None,
            mode: str | None,
        ) -> None:
            """Run a Sling replication.

            Execute a data replication using Sling. Either provide a replication
            YAML configuration file or specify source/target/stream parameters
            for ad-hoc execution.

            Args:
                replication: Path to a Sling replication YAML file.
                source: Source connection name (for ad-hoc runs).
                target: Target connection name (for ad-hoc runs).
                stream: Source stream identifier (e.g., "public.users").
                target_object: Target object/table name.
                mode: Replication mode override.

            Raises:
                click.UsageError: If neither replication file nor source/stream
                    parameters are provided.

            """
            from sling import Replication, Sling

            apply_sling_connection_env()
            resolved_mode = mode or get_settings().sling_default_mode

            if replication:
                click.echo(f"Running replication from {replication}")
                repl = Replication(file_path=replication)
                repl.run()
            elif source and stream:
                if not target:
                    raise click.UsageError("Provide --target for ad-hoc runs.")
                resolved_target_object = _resolve_target_object(stream=stream, target_object=target_object)
                click.echo(f"Replicating {stream} from {source}")
                config = Sling(
                    src_conn=source,
                    src_stream=stream,
                    tgt_conn=target,
                    tgt_object=resolved_target_object,
                    mode=resolved_mode,
                )
                config.run()
            else:
                raise click.UsageError("Provide --replication YAML or --source/--stream.")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;replication&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Path to a Sling replication YAML file.
        </PyParameter>

        <PyParameter name="&#x22;source&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Source connection name (for ad-hoc runs).
        </PyParameter>

        <PyParameter name="&#x22;target&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Target connection name (for ad-hoc runs).
        </PyParameter>

        <PyParameter name="&#x22;stream&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Source stream identifier (e.g., "public.users").
        </PyParameter>

        <PyParameter name="&#x22;target_object&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Target object/table name.
        </PyParameter>

        <PyParameter name="&#x22;mode&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Replication mode override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;conns_command&#x22;" type="&#x22;(auto) -> None&#x22;">
      List available Sling connections.

      Shows auto-discovered connections from Phlo capability metadata and any
      connections from explicit env.yaml files. This helps verify that Phlo
      packages are properly configured and connections are available.

      <PySourceCode>
        ```python
        @sling_group.command("conns")
        @click.option("--auto/--no-auto", default=True, help="Include auto-discovered connections.")
        def conns_command(auto: bool) -> None:
            """List available Sling connections.

            Shows auto-discovered connections from Phlo capability metadata and any
            connections from explicit env.yaml files. This helps verify that Phlo
            packages are properly configured and connections are available.

            Args:
                auto: Whether to include auto-discovered Phlo connections.

            """
            if auto:
                from phlo_sling.connections import resolve_phlo_connections

                connections = resolve_phlo_connections()
                if connections:
                    click.echo("Auto-discovered connections:")
                    for name, config in connections.items():
                        conn_type = config.get("type", "unknown")
                        host = config.get("host") or config.get("endpoint", "")
                        click.echo(f"  {name}: {conn_type} ({host})")
                else:
                    click.echo("No auto-discovered connections found.")

            click.echo("\nSling native connections:")
            try:
                result = _run_sling_cli_command(["conns", "list"])
                click.echo(result.stdout, nl=False)
            except Exception as exc:
                click.echo(f"  Could not list native connections: {exc}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;auto&#x22;" type="&#x22;bool&#x22;" value="undefined">
          Whether to include auto-discovered Phlo connections.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;discover_command&#x22;" type="&#x22;(connection, schema, output_format) -> None&#x22;">
      Discover available streams from a Sling connection.

      Lists tables/views available in the source connection for use as
      stream\_name in @phlo\_sling\_replication decorators. This is useful
      for exploring source databases before defining replications.

      <PySourceCode>
        ```python
        @sling_group.command("discover")
        @click.argument("connection")
        @click.option("--schema", help="Filter by schema name.")
        @click.option(
            "--format",
            "output_format",
            type=click.Choice(["table", "json"]),
            default="table",
            show_default=True,
            help="Output format.",
        )
        def discover_command(connection: str, schema: str | None, output_format: str) -> None:
            """Discover available streams from a Sling connection.

            Lists tables/views available in the source connection for use as
            stream_name in @phlo_sling_replication decorators. This is useful
            for exploring source databases before defining replications.

            Args:
                connection: Connection name to discover streams from.
                schema: Optional schema name filter (uses pattern matching).
                output_format: Output format - "table" or "json".

            Raises:
                click.ClickException: If discovery fails.

            """
            apply_sling_connection_env()

            click.echo(f"Discovering streams from {connection}...")
            try:
                command = ["conns", "discover", connection]
                if schema:
                    command.extend(["--pattern", f"{schema}.*"])

                result = _run_sling_cli_command(command)
                if output_format == "json":
                    click.echo(json.dumps(_parse_discovery_output(result.stdout), indent=2))
                    return

                click.echo(result.stdout, nl=False)
            except Exception as exc:
                raise click.ClickException(f"Discovery failed: {exc}") from exc
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;connection&#x22;" type="&#x22;str&#x22;" value="undefined">
          Connection name to discover streams from.
        </PyParameter>

        <PyParameter name="&#x22;schema&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Optional schema name filter (uses pattern matching).
        </PyParameter>

        <PyParameter name="&#x22;output_format&#x22;" type="&#x22;str&#x22;" value="undefined">
          Output format - "table" or "json".
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_resolve_target_object&#x22;" type="&#x22;(stream, target_object) -> str&#x22;">
      Resolve the destination object for an ad-hoc Sling run.

      Determines the target object name from the stream or explicit parameter.
      Rejects wildcards without explicit target specification.

      <PySourceCode>
        ```python
        def _resolve_target_object(stream: str, target_object: str | None) -> str:
            """Resolve the destination object for an ad-hoc Sling run.

            Determines the target object name from the stream or explicit parameter.
            Rejects wildcards without explicit target specification.

            Args:
                stream: Source stream identifier.
                target_object: Optional explicit target object name.

            Returns:
                Resolved target object name.

            Raises:
                click.UsageError: If stream contains wildcard without explicit target.

            """
            if target_object:
                return target_object
            if "*" in stream:
                raise click.UsageError("Provide --object when --stream uses a wildcard.")
            return stream
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;stream&#x22;" type="&#x22;str&#x22;" value="undefined">
          Source stream identifier.
        </PyParameter>

        <PyParameter name="&#x22;target_object&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Optional explicit target object name.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Resolved target object name.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_get_sling_binary&#x22;" type="&#x22;() -> str&#x22;">
      Return the Sling binary path, honoring package settings.

      Checks for an override in settings first, then falls back to the
      bundled binary from the sling package.

      <PySourceCode>
        ```python
        def _get_sling_binary() -> str:
            """Return the Sling binary path, honoring package settings.

            Checks for an override in settings first, then falls back to the
            bundled binary from the sling package.

            Returns:
                Path to the Sling binary executable.

            Raises:
                ImportError: If sling package is not installed.

            """
            settings = get_settings()
            if settings.sling_binary_path:
                return settings.sling_binary_path

            from sling.bin import SLING_BIN

            return SLING_BIN
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Path to the Sling binary executable.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_run_sling_cli_command&#x22;" type="&#x22;(args) -> subprocess.CompletedProcess[str]&#x22;">
      Execute the Sling CLI and return captured output.

      Runs a Sling CLI command with the specified arguments and captures
      stdout/stderr.

      <PySourceCode>
        ```python
        def _run_sling_cli_command(args: list[str]) -> subprocess.CompletedProcess[str]:
            """Execute the Sling CLI and return captured output.

            Runs a Sling CLI command with the specified arguments and captures
            stdout/stderr.

            Args:
                args: List of command arguments (not including binary path).

            Returns:
                CompletedProcess with stdout and stderr captured.

            Raises:
                subprocess.CalledProcessError: If the command exits non-zero.

            """
            return subprocess.run(
                [_get_sling_binary(), *args],
                check=True,
                capture_output=True,
                text=True,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;args&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
          List of command arguments (not including binary path).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;subprocess.CompletedProcess&#x22;">
        CompletedProcess with stdout and stderr captured.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_parse_discovery_output&#x22;" type="&#x22;(output) -> list[dict[str, str]]&#x22;">
      Parse Sling's ASCII discovery table into JSON-serializable rows.

      Converts the ASCII table output from Sling's discover command into
      a list of dictionaries suitable for JSON serialization.

      <PySourceCode>
        ```python
        def _parse_discovery_output(output: str) -> list[dict[str, str]]:
            """Parse Sling's ASCII discovery table into JSON-serializable rows.

            Converts the ASCII table output from Sling's discover command into
            a list of dictionaries suitable for JSON serialization.

            Args:
                output: Raw ASCII table output from Sling discover.

            Returns:
                List of dictionaries with normalized column headers as keys.

            """
            lines = [line.rstrip() for line in output.splitlines() if line.strip()]
            table_lines = [line for line in lines if "|" in line]
            if len(table_lines) < 2:
                return []

            headers = [_normalize_column_name(part) for part in table_lines[0].split("|")]
            rows: list[dict[str, str]] = []
            for line in table_lines[1:]:
                values = [part.strip() for part in line.split("|")]
                if len(values) != len(headers):
                    continue
                if all(set(value) <= {"-"} for value in values):
                    continue
                rows.append(dict(zip(headers, values, strict=True)))

            return rows
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;output&#x22;" type="&#x22;str&#x22;" value="undefined">
          Raw ASCII table output from Sling discover.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of dictionaries with normalized column headers as keys.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_normalize_column_name&#x22;" type="&#x22;(value) -> str&#x22;">
      Normalize discovery table headers for JSON output.

      Converts column headers from Sling's table format to snake\_case
      suitable for JSON keys.

      <PySourceCode>
        ```python
        def _normalize_column_name(value: str) -> str:
            """Normalize discovery table headers for JSON output.

            Converts column headers from Sling's table format to snake_case
            suitable for JSON keys.

            Args:
                value: Raw column header string.

            Returns:
                Normalized snake_case column name.

            """
            return value.strip().lower().replace(" ", "_")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;str&#x22;" value="undefined">
          Raw column header string.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Normalized snake\_case column name.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
