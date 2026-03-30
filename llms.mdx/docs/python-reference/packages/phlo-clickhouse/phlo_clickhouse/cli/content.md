# cli (/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/cli)



CLI commands for the ClickHouse data plane service.

This module provides command-line interface commands for interacting with
ClickHouse services, including SQL query execution and status monitoring.

Example:
Using the CLI commands:

$ phlo clickhouse query "SELECT version()"
24.3.0

$ phlo clickhouse status
version: 24.3.0
uptime\_seconds: 3600
current\_database: default

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_read_query&#x22;" type="&#x22;(*, query, file) -> str&#x22;">
      Read and validate SQL query from inline string or file.

      Extracts SQL text from either an inline query string or a file path.
      Validates that exactly one source is provided and the content is non-empty.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > from pathlib import Path
        > > > \_read\_query(query="SELECT 1", file=None)
        > > > 'SELECT 1'
      </Callout>

      <PySourceCode>
        ```python
        def _read_query(*, query: str | None, file: Path | None) -> str:
            """Read and validate SQL query from inline string or file.

            Extracts SQL text from either an inline query string or a file path.
            Validates that exactly one source is provided and the content is non-empty.

            Args:
                query: Inline SQL query string, or None if using file.
                file: Path to SQL file, or None if using inline query.

            Returns:
                Validated SQL query string with whitespace stripped.

            Raises:
                click.ClickException: If both query and file are provided,
                    if file cannot be read, if file is empty, or if neither is provided.

            Example:
                >>> from pathlib import Path
                >>> _read_query(query="SELECT 1", file=None)
                'SELECT 1'

            """
            if query and file:
                raise click.ClickException("Use either an inline query or --file, not both.")
            if file is not None:
                try:
                    sql = file.read_text(encoding="utf-8")
                except OSError as exc:
                    raise click.ClickException(f"Failed to read SQL file: {file}") from exc
                if sql.strip():
                    return sql
                raise click.ClickException(f"SQL file is empty: {file}")
            if query and query.strip():
                return query
            raise click.ClickException("Provide a SQL query argument or --file.")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;query&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Inline SQL query string, or None if using file.
        </PyParameter>

        <PyParameter name="&#x22;file&#x22;" type="&#x22;Path | None&#x22;" value="undefined">
          Path to SQL file, or None if using inline query.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Validated SQL query string with whitespace stripped.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_ensure_phlo_dir&#x22;" type="&#x22;() -> Path&#x22;">
      Verify and return the Phlo project directory.

      Checks for the presence of a .phlo directory in the current working directory,
      which indicates a valid Phlo project.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > In a directory with .phlo/ subdirectory [#in-a-directory-with-phlo-subdirectory]
        > > >
        > > > path = \_ensure\_phlo\_dir()
        > > > path.name
        > > > '.phlo'
      </Callout>

      <PySourceCode>
        ```python
        def _ensure_phlo_dir() -> Path:
            """Verify and return the Phlo project directory.

            Checks for the presence of a .phlo directory in the current working directory,
            which indicates a valid Phlo project.

            Returns:
                Path to the .phlo directory.

            Raises:
                click.ClickException: If the .phlo directory does not exist.

            Example:
                >>> # In a directory with .phlo/ subdirectory
                >>> path = _ensure_phlo_dir()
                >>> path.name
                '.phlo'

            """
            phlo_dir = Path.cwd() / ".phlo"
            if phlo_dir.exists():
                return phlo_dir
            raise click.ClickException(".phlo directory not found. Run 'phlo services init' first.")
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;">
        Path to the .phlo directory.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_require_docker&#x22;" type="&#x22;() -> None&#x22;">
      Validate Docker installation and daemon status.

      Verifies that Docker is installed on the system and the Docker daemon
      is running and responsive.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > \_require\_docker()  # Raises exception if Docker unavailable
      </Callout>

      <PySourceCode>
        ```python
        def _require_docker() -> None:
            """Validate Docker installation and daemon status.

            Verifies that Docker is installed on the system and the Docker daemon
            is running and responsive.

            Raises:
                click.ClickException: If Docker is not installed, not in PATH,
                    or if the Docker daemon is not running.

            Example:
                >>> _require_docker()  # Raises exception if Docker unavailable

            """
            if which("docker") is None:
                raise click.ClickException("docker command not found.")
            try:
                result = run_command(
                    ["docker", "info"],
                    timeout_seconds=10,
                    capture_output=True,
                    check=False,
                )
            except TimeoutExpired as exc:
                raise click.ClickException("docker info timed out.") from exc
            if result.returncode == 0:
                return
            raise click.ClickException("Docker is not running.")
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;clickhouse_group&#x22;" type="&#x22;() -> None&#x22;">
      Query and inspect the ClickHouse data plane service.

      This command group provides tools for interacting with ClickHouse,
      including SQL query execution and service status monitoring.

      Example:
      $ phlo clickhouse --help
      $ phlo clickhouse query "SELECT 1"

      <PySourceCode>
        ```python
        @click.group(name="clickhouse")
        def clickhouse_group() -> None:
            """Query and inspect the ClickHouse data plane service.

            This command group provides tools for interacting with ClickHouse,
            including SQL query execution and service status monitoring.

            Example:
                $ phlo clickhouse --help
                $ phlo clickhouse query "SELECT 1"

            """
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;clickhouse_query&#x22;" type="&#x22;(query, query_file, output_format, timeout_seconds) -> None&#x22;">
      Execute a SQL query against the running ClickHouse service.

      Runs the specified SQL query against ClickHouse using the clickhouse-client
      utility within the Docker container. Results are printed to stdout.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo clickhouse query "SELECT version()"
        $ phlo clickhouse query --file queries/analysis.sql --format CSV
      </Callout>

      <PySourceCode>
        ```python
        @clickhouse_group.command(name="query")
        @click.argument("query", required=False)
        @click.option(
            "--file",
            "query_file",
            type=click.Path(exists=True, dir_okay=False, path_type=Path),
            help="Path to SQL file containing the query to execute.",
        )
        @click.option(
            "--format",
            "output_format",
            default="TabSeparatedRaw",
            show_default=True,
            help="Output format for query results (e.g., TabSeparatedRaw, JSON, CSV).",
        )
        @click.option(
            "--timeout",
            "timeout_seconds",
            default=30,
            show_default=True,
            type=int,
            help="Query execution timeout in seconds.",
        )
        def clickhouse_query(
            query: str | None,
            query_file: Path | None,
            output_format: str,
            timeout_seconds: int,
        ) -> None:
            """Execute a SQL query against the running ClickHouse service.

            Runs the specified SQL query against ClickHouse using the clickhouse-client
            utility within the Docker container. Results are printed to stdout.

            Args:
                query: SQL query string provided as command argument.
                query_file: Path to file containing SQL query (alternative to query arg).
                output_format: Format string for result output (ClickHouse format name).
                timeout_seconds: Maximum time to wait for query execution.

            Raises:
                click.ClickException: If Docker is unavailable, query fails, or times out.

            Example:
                $ phlo clickhouse query "SELECT version()"
                $ phlo clickhouse query --file queries/analysis.sql --format CSV

            """
            _require_docker()
            phlo_dir = _ensure_phlo_dir()
            project_name = get_project_name()
            sql = _read_query(query=query, file=query_file)

            cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
            cmd.extend(
                [
                    "exec",
                    "-T",
                    "clickhouse",
                    "clickhouse-client",
                    "--multiquery",
                    "--format",
                    output_format,
                    "--query",
                    sql,
                ]
            )

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
                raise click.ClickException(f"Query timed out after {timeout_seconds} seconds.") from exc

            if result.stdout:
                click.echo(result.stdout, nl=False)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;query&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          SQL query string provided as command argument.
        </PyParameter>

        <PyParameter name="&#x22;query_file&#x22;" type="&#x22;Path | None&#x22;" value="undefined">
          Path to file containing SQL query (alternative to query arg).
        </PyParameter>

        <PyParameter name="&#x22;output_format&#x22;" type="&#x22;str&#x22;" value="undefined">
          Format string for result output (ClickHouse format name).
        </PyParameter>

        <PyParameter name="&#x22;timeout_seconds&#x22;" type="&#x22;int&#x22;" value="undefined">
          Maximum time to wait for query execution.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;clickhouse_status&#x22;" type="&#x22;() -> None&#x22;">
      Show ClickHouse service status and basic server info.

      Displays version, uptime, and current database information from the
      running ClickHouse service.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo clickhouse status
        version    uptime\_seconds    current\_database
        24.3.0     3600              default
      </Callout>

      <PySourceCode>
        ```python
        @clickhouse_group.command(name="status")
        def clickhouse_status() -> None:
            """Show ClickHouse service status and basic server info.

            Displays version, uptime, and current database information from the
            running ClickHouse service.

            Raises:
                click.ClickException: If Docker is unavailable or status check fails.

            Example:
                $ phlo clickhouse status
                version    uptime_seconds    current_database
                24.3.0     3600              default

            """
            _require_docker()
            phlo_dir = _ensure_phlo_dir()
            project_name = get_project_name()

            cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
            cmd.extend(
                [
                    "exec",
                    "-T",
                    "clickhouse",
                    "clickhouse-client",
                    "--query",
                    "SELECT version() AS version, uptime() AS uptime_seconds, "
                    "currentDatabase() AS current_database",
                ]
            )

            try:
                result = run_command(
                    cmd,
                    timeout_seconds=10,
                    capture_output=True,
                    check=True,
                )
            except CommandError as exc:
                stderr = exc.stderr.strip()
                raise click.ClickException(stderr or str(exc)) from exc
            except TimeoutExpired as exc:
                raise click.ClickException("Status check timed out.") from exc

            if result.stdout:
                click.echo(result.stdout, nl=False)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
