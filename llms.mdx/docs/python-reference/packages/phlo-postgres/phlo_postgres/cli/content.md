# cli (/docs/python-reference/packages/phlo-postgres/phlo_postgres/cli)



CLI commands for PostgreSQL service management.

This module provides Click-based CLI commands for interacting with the PostgreSQL
service, including running queries, dumping/restoring databases, and performing
maintenance operations like vacuuming.

All commands execute within the PostgreSQL Docker container via docker compose exec.

Example:
$ phlo postgres query "SELECT \* FROM users LIMIT 10"
$ phlo postgres dump --file backup.sql.gz
$ phlo postgres restore --file backup.sql.gz
$ phlo postgres vacuum --analyze

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_read_sql&#x22;" type="&#x22;(*, query, file) -> str&#x22;">
      Read SQL from inline query string or file path.

      Validates that exactly one of query or file is provided and returns the
      SQL content. Handles empty file detection and encoding issues.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > sql = \_read\_sql(query="SELECT 1")
        > > > sql = \_read\_sql(file=Path("query.sql"))
      </Callout>

      <PySourceCode>
        ```python
        def _read_sql(*, query: str | None, file: Path | None) -> str:
            """Read SQL from inline query string or file path.

            Validates that exactly one of query or file is provided and returns the
            SQL content. Handles empty file detection and encoding issues.

            Args:
                query: Inline SQL query string.
                file: Path to SQL file to read.

            Returns:
                str: The SQL content to execute.

            Raises:
                click.ClickException: If both query and file are provided, neither is
                    provided, or the file is empty/cannot be read.

            Example:
                >>> sql = _read_sql(query="SELECT 1")
                >>> sql = _read_sql(file=Path("query.sql"))

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
          Inline SQL query string.
        </PyParameter>

        <PyParameter name="&#x22;file&#x22;" type="&#x22;Path | None&#x22;" value="undefined">
          Path to SQL file to read.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        The SQL content to execute.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_require_docker&#x22;" type="&#x22;() -> None&#x22;">
      Validate that the Docker CLI is installed and available.

      Checks for the presence of the 'docker' command in the system PATH.
      This is a prerequisite for all PostgreSQL CLI commands.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > \_require\_docker()  # Raises if docker not installed
      </Callout>

      <PySourceCode>
        ```python
        def _require_docker() -> None:
            """Validate that the Docker CLI is installed and available.

            Checks for the presence of the 'docker' command in the system PATH.
            This is a prerequisite for all PostgreSQL CLI commands.

            Raises:
                click.ClickException: If the docker command is not found in PATH.

            Example:
                >>> _require_docker()  # Raises if docker not installed

            """
            if which("docker") is None:
                raise click.ClickException("docker command not found.")
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_postgres_exec_base&#x22;" type="&#x22;(*, tty) -> list[str]&#x22;">
      Build the docker compose exec base command for PostgreSQL container.

      Constructs the initial portion of the docker compose exec command including
      project name and service name. Used as a base for all container operations.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > cmd = \_postgres\_exec\_base(tty=True)
        > > >
        > > > Returns: ['docker', 'compose', '-p', 'phlo', '-f', '...', 'exec', '-t', 'postgres'] [#returns-docker-compose--p-phlo--f--exec--t-postgres]
      </Callout>

      <PySourceCode>
        ```python
        def _postgres_exec_base(*, tty: bool) -> list[str]:
            """Build the docker compose exec base command for PostgreSQL container.

            Constructs the initial portion of the docker compose exec command including
            project name and service name. Used as a base for all container operations.

            Args:
                tty: Whether to allocate a TTY (-t flag). Disable for non-interactive
                    commands that capture output.

            Returns:
                list[str]: Base command as a list of strings ready for subprocess.

            Example:
                >>> cmd = _postgres_exec_base(tty=True)
                >>> # Returns: ['docker', 'compose', '-p', 'phlo', '-f', '...', 'exec', '-t', 'postgres']

            """
            phlo_dir = ensure_phlo_dir()
            project_name = get_project_name()
            cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
            cmd.append("exec")
            if not tty:
                cmd.append("-T")
            cmd.append("postgres")
            return cmd
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;tty&#x22;" type="&#x22;bool&#x22;" value="undefined">
          Whether to allocate a TTY (-t flag). Disable for non-interactive
          commands that capture output.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        list\[str]: Base command as a list of strings ready for subprocess.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_postgres_identity&#x22;" type="&#x22;(*, user, database) -> tuple[str, str]&#x22;">
      Resolve PostgreSQL connection identity (user and database).

      Returns explicit values if provided, otherwise falls back to settings
      defaults. This allows CLI commands to use configured defaults while
      permitting overrides.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > user, db = \_postgres\_identity(user=None, database=None)
        > > >
        > > > Uses settings.postgres_user and settings.postgres_db [#uses-settingspostgres_user-and-settingspostgres_db]
        > > >
        > > > user, db = \_postgres\_identity(user="admin", database=None)
        > > >
        > > > Uses "admin" for user, settings default for database [#uses-admin-for-user-settings-default-for-database]
      </Callout>

      <PySourceCode>
        ```python
        def _postgres_identity(*, user: str | None, database: str | None) -> tuple[str, str]:
            """Resolve PostgreSQL connection identity (user and database).

            Returns explicit values if provided, otherwise falls back to settings
            defaults. This allows CLI commands to use configured defaults while
            permitting overrides.

            Args:
                user: Database username override, or None to use settings default.
                database: Database name override, or None to use settings default.

            Returns:
                tuple[str, str]: Tuple of (resolved_user, resolved_database).

            Example:
                >>> user, db = _postgres_identity(user=None, database=None)
                >>> # Uses settings.postgres_user and settings.postgres_db
                >>> user, db = _postgres_identity(user="admin", database=None)
                >>> # Uses "admin" for user, settings default for database

            """
            settings = get_settings()
            return user or settings.postgres_user, database or settings.postgres_db
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;user&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Database username override, or None to use settings default.
        </PyParameter>

        <PyParameter name="&#x22;database&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Database name override, or None to use settings default.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;tuple&#x22;">
        tuple\[str, str]: Tuple of (resolved\_user, resolved\_database).
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;postgres_group&#x22;" type="&#x22;(ctx, postgres_args) -> None&#x22;">
      Run psql or PostgreSQL helper commands against the project database.

      This is the main entry point for PostgreSQL CLI operations. It supports:

      * Interactive psql sessions (default if no subcommand)
      * Subcommands: query, dump, restore, vacuum
      * Direct psql arguments passthrough

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo postgres                    # Interactive psql
        $ phlo postgres -c "SELECT 1"       # One-off query via psql
        $ phlo postgres query "SELECT \* FROM users"
        $ phlo postgres dump --file backup.sql.gz
      </Callout>

      <PySourceCode>
        ```python
        @click.command(
            name="postgres",
            context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
        )
        @click.argument("postgres_args", nargs=-1, type=click.UNPROCESSED)
        @click.pass_context
        def postgres_group(ctx: click.Context, postgres_args: tuple[str, ...]) -> None:
            """Run psql or PostgreSQL helper commands against the project database.

            This is the main entry point for PostgreSQL CLI operations. It supports:
            - Interactive psql sessions (default if no subcommand)
            - Subcommands: query, dump, restore, vacuum
            - Direct psql arguments passthrough

            Args:
                ctx: Click context object.
                postgres_args: Additional arguments passed to psql or subcommands.

            Example:
                $ phlo postgres                    # Interactive psql
                $ phlo postgres -c "SELECT 1"       # One-off query via psql
                $ phlo postgres query "SELECT * FROM users"
                $ phlo postgres dump --file backup.sql.gz

            """
            if postgres_args and postgres_args[0] == "query":
                postgres_query.main(
                    args=list(postgres_args[1:]),
                    prog_name="phlo postgres query",
                    standalone_mode=False,
                )
                return
            if postgres_args and postgres_args[0] == "dump":
                postgres_dump.main(
                    args=list(postgres_args[1:]),
                    prog_name="phlo postgres dump",
                    standalone_mode=False,
                )
                return
            if postgres_args and postgres_args[0] == "restore":
                postgres_restore.main(
                    args=list(postgres_args[1:]),
                    prog_name="phlo postgres restore",
                    standalone_mode=False,
                )
                return
            if postgres_args and postgres_args[0] == "vacuum":
                postgres_vacuum.main(
                    args=list(postgres_args[1:]),
                    prog_name="phlo postgres vacuum",
                    standalone_mode=False,
                )
                return

            _require_docker()
            user, database = _postgres_identity(user=None, database=None)
            cmd = _postgres_exec_base(tty=True)
            cmd.extend(["psql", "-U", user, "-d", database])
            cmd.extend(postgres_args)
            result = subprocess.run(cmd, check=False)
            if result.returncode != 0:
                raise click.ClickException(f"psql exited with status {result.returncode}.")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;ctx&#x22;" type="&#x22;click.Context&#x22;" value="undefined">
          Click context object.
        </PyParameter>

        <PyParameter name="&#x22;postgres_args&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="undefined">
          Additional arguments passed to psql or subcommands.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;postgres_query&#x22;" type="&#x22;(query, query_file, user, database, timeout_seconds) -> None&#x22;">
      Execute a SQL query against the running PostgreSQL service.

      Executes a SQL query inside the PostgreSQL container and prints results
      to stdout. Supports inline queries or reading from a file.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo postgres query "SELECT \* FROM users"
        $ phlo postgres query --file query.sql --timeout 60
      </Callout>

      <PySourceCode>
        ```python
        @click.command(name="query")
        @click.argument("query", required=False)
        @click.option(
            "--file",
            "query_file",
            type=click.Path(exists=True, dir_okay=False, path_type=Path),
        )
        @click.option("--user", default=None, help="Database user.")
        @click.option("--db", "database", default=None, help="Database name.")
        @click.option("--timeout", "timeout_seconds", default=30, show_default=True, type=int)
        def postgres_query(
            query: str | None,
            query_file: Path | None,
            user: str | None,
            database: str | None,
            timeout_seconds: int,
        ) -> None:
            """Execute a SQL query against the running PostgreSQL service.

            Executes a SQL query inside the PostgreSQL container and prints results
            to stdout. Supports inline queries or reading from a file.

            Args:
                query: SQL query string to execute.
                query_file: Path to file containing SQL query.
                user: Database user (default from settings).
                database: Database name (default from settings).
                timeout_seconds: Maximum time to wait for query completion.

            Raises:
                click.ClickException: If the query fails or times out.

            Example:
                $ phlo postgres query "SELECT * FROM users"
                $ phlo postgres query --file query.sql --timeout 60

            """
            _require_docker()
            sql = _read_sql(query=query, file=query_file)
            resolved_user, resolved_db = _postgres_identity(user=user, database=database)
            cmd = _postgres_exec_base(tty=False)
            cmd.extend(["psql", "-U", resolved_user, "-d", resolved_db, "-v", "ON_ERROR_STOP=1", "-c", sql])

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
          SQL query string to execute.
        </PyParameter>

        <PyParameter name="&#x22;query_file&#x22;" type="&#x22;Path | None&#x22;" value="undefined">
          Path to file containing SQL query.
        </PyParameter>

        <PyParameter name="&#x22;user&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Database user (default from settings).
        </PyParameter>

        <PyParameter name="&#x22;database&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Database name (default from settings).
        </PyParameter>

        <PyParameter name="&#x22;timeout_seconds&#x22;" type="&#x22;int&#x22;" value="undefined">
          Maximum time to wait for query completion.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;postgres_dump&#x22;" type="&#x22;(output_file, user, database, timeout_seconds) -> None&#x22;">
      Create a PostgreSQL logical backup (pg\_dump) to a local file.

      Dumps the entire database using pg\_dump, with optional gzip compression
      if the output file has a .gz extension.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo postgres dump --file backup.sql
        $ phlo postgres dump --file backup.sql.gz --timeout 300
      </Callout>

      <PySourceCode>
        ```python
        @click.command(name="dump")
        @click.option(
            "--file",
            "output_file",
            type=click.Path(dir_okay=False, path_type=Path),
            required=True,
            help="Output path. Use .gz for gzip-compressed dumps.",
        )
        @click.option("--user", default=None, help="Database user.")
        @click.option("--db", "database", default=None, help="Database name.")
        @click.option("--timeout", "timeout_seconds", default=120, show_default=True, type=int)
        def postgres_dump(
            output_file: Path,
            user: str | None,
            database: str | None,
            timeout_seconds: int,
        ) -> None:
            """Create a PostgreSQL logical backup (pg_dump) to a local file.

            Dumps the entire database using pg_dump, with optional gzip compression
            if the output file has a .gz extension.

            Args:
                output_file: Path to write the dump. Use .gz extension for compression.
                user: Database user (default from settings).
                database: Database name (default from settings).
                timeout_seconds: Maximum time to wait for dump completion.

            Raises:
                click.ClickException: If the dump fails or times out.

            Example:
                $ phlo postgres dump --file backup.sql
                $ phlo postgres dump --file backup.sql.gz --timeout 300

            """
            _require_docker()
            resolved_user, resolved_db = _postgres_identity(user=user, database=database)
            cmd = _postgres_exec_base(tty=False)
            cmd.extend(["pg_dump", "-U", resolved_user, resolved_db])

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
                raise click.ClickException(f"Dump timed out after {timeout_seconds} seconds.") from exc

            output_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                if output_file.suffix == ".gz":
                    with gzip.open(output_file, "wt", encoding="utf-8") as handle:
                        handle.write(result.stdout)
                else:
                    output_file.write_text(result.stdout, encoding="utf-8")
            except OSError as exc:
                raise click.ClickException(f"Failed to write dump file: {output_file}") from exc

            click.echo(f"Wrote dump to {output_file}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;output_file&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to write the dump. Use .gz extension for compression.
        </PyParameter>

        <PyParameter name="&#x22;user&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Database user (default from settings).
        </PyParameter>

        <PyParameter name="&#x22;database&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Database name (default from settings).
        </PyParameter>

        <PyParameter name="&#x22;timeout_seconds&#x22;" type="&#x22;int&#x22;" value="undefined">
          Maximum time to wait for dump completion.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;postgres_restore&#x22;" type="&#x22;(input_file, user, database, timeout_seconds) -> None&#x22;">
      Restore a PostgreSQL database from a logical backup file.

      Restores the database from a SQL dump file (plain or gzip-compressed).
      Uses psql internally to execute the dump SQL.

      <Callout title="&#x22;Warning&#x22;" type="&#x22;warning&#x22;">
        This may overwrite existing data. Use with caution on production databases.
      </Callout>

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo postgres restore --file backup.sql
        $ phlo postgres restore --file backup.sql.gz --db mydb --timeout 600
      </Callout>

      <PySourceCode>
        ```python
        @click.command(name="restore")
        @click.option(
            "--file",
            "input_file",
            type=click.Path(exists=True, dir_okay=False, path_type=Path),
            required=True,
            help="Input dump file. Supports .sql and .gz files.",
        )
        @click.option("--user", default=None, help="Database user.")
        @click.option("--db", "database", default=None, help="Database name.")
        @click.option("--timeout", "timeout_seconds", default=120, show_default=True, type=int)
        def postgres_restore(
            input_file: Path,
            user: str | None,
            database: str | None,
            timeout_seconds: int,
        ) -> None:
            """Restore a PostgreSQL database from a logical backup file.

            Restores the database from a SQL dump file (plain or gzip-compressed).
            Uses psql internally to execute the dump SQL.

            Warning:
                This may overwrite existing data. Use with caution on production databases.

            Args:
                input_file: Path to the dump file (.sql or .sql.gz).
                user: Database user (default from settings).
                database: Database name (default from settings).
                timeout_seconds: Maximum time to wait for restore completion.

            Raises:
                click.ClickException: If the restore fails or times out.

            Example:
                $ phlo postgres restore --file backup.sql
                $ phlo postgres restore --file backup.sql.gz --db mydb --timeout 600

            """
            _require_docker()
            resolved_user, resolved_db = _postgres_identity(user=user, database=database)
            cmd = _postgres_exec_base(tty=False)
            cmd.extend(["psql", "-U", resolved_user, "-d", resolved_db, "-v", "ON_ERROR_STOP=1"])

            try:
                if input_file.suffix == ".gz":
                    with gzip.open(input_file, "rt", encoding="utf-8") as handle:
                        sql = handle.read()
                else:
                    sql = input_file.read_text(encoding="utf-8")
            except OSError as exc:
                raise click.ClickException(f"Failed to read restore file: {input_file}") from exc

            try:
                result = subprocess.run(
                    cmd,
                    input=sql,
                    text=True,
                    capture_output=True,
                    timeout=timeout_seconds,
                    check=False,
                )
            except TimeoutExpired as exc:
                raise click.ClickException(f"Restore timed out after {timeout_seconds} seconds.") from exc

            if result.returncode != 0:
                stderr = (result.stderr or "").strip()
                raise click.ClickException(stderr or f"Restore failed with status {result.returncode}.")

            click.echo(f"Restored {input_file} into {resolved_db}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;input_file&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to the dump file (.sql or .sql.gz).
        </PyParameter>

        <PyParameter name="&#x22;user&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Database user (default from settings).
        </PyParameter>

        <PyParameter name="&#x22;database&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Database name (default from settings).
        </PyParameter>

        <PyParameter name="&#x22;timeout_seconds&#x22;" type="&#x22;int&#x22;" value="undefined">
          Maximum time to wait for restore completion.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;postgres_vacuum&#x22;" type="&#x22;(user, database, analyze, timeout_seconds) -> None&#x22;">
      Run vacuumdb for PostgreSQL maintenance inside the container.

      Executes vacuumdb to reclaim storage and optionally update statistics.
      This is useful for routine database maintenance after large operations.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo postgres vacuum
        $ phlo postgres vacuum --no-analyze
        $ phlo postgres vacuum --db analytics --timeout 300
      </Callout>

      <PySourceCode>
        ```python
        @click.command(name="vacuum")
        @click.option("--user", default=None, help="Database user.")
        @click.option("--db", "database", default=None, help="Database name.")
        @click.option("--analyze/--no-analyze", default=True, show_default=True)
        @click.option("--timeout", "timeout_seconds", default=120, show_default=True, type=int)
        def postgres_vacuum(
            user: str | None,
            database: str | None,
            analyze: bool,
            timeout_seconds: int,
        ) -> None:
            """Run vacuumdb for PostgreSQL maintenance inside the container.

            Executes vacuumdb to reclaim storage and optionally update statistics.
            This is useful for routine database maintenance after large operations.

            Args:
                user: Database user (default from settings).
                database: Database name (default from settings).
                analyze: Whether to run ANALYZE after vacuum (updates statistics).
                timeout_seconds: Maximum time to wait for vacuum completion.

            Raises:
                click.ClickException: If vacuum fails or times out.

            Example:
                $ phlo postgres vacuum
                $ phlo postgres vacuum --no-analyze
                $ phlo postgres vacuum --db analytics --timeout 300

            """
            _require_docker()
            resolved_user, resolved_db = _postgres_identity(user=user, database=database)
            cmd = _postgres_exec_base(tty=False)
            cmd.extend(["vacuumdb", "-U", resolved_user])
            if analyze:
                cmd.append("-z")
            cmd.append(resolved_db)

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
                raise click.ClickException(f"Vacuum timed out after {timeout_seconds} seconds.") from exc

            if result.stdout:
                click.echo(result.stdout, nl=False)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;user&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Database user (default from settings).
        </PyParameter>

        <PyParameter name="&#x22;database&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Database name (default from settings).
        </PyParameter>

        <PyParameter name="&#x22;analyze&#x22;" type="&#x22;bool&#x22;" value="undefined">
          Whether to run ANALYZE after vacuum (updates statistics).
        </PyParameter>

        <PyParameter name="&#x22;timeout_seconds&#x22;" type="&#x22;int&#x22;" value="undefined">
          Maximum time to wait for vacuum completion.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
