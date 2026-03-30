# cli (/docs/python-reference/packages/phlo-trino/phlo_trino/cli)



CLI commands for the Trino query engine service.

This module provides CLI commands for interacting with Trino, including:

* Running the Trino interactive shell
* Executing SQL queries from command line or files
* Managing query output formats and timeouts

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_read_query&#x22;" type="&#x22;(*, query, file) -> str&#x22;">
      Return SQL text from inline query or file input.

      <PySourceCode>
        ```python
        def _read_query(*, query: str | None, file: Path | None) -> str:
            """Return SQL text from inline query or file input."""
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
        <PyParameter name="&#x22;query&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;file&#x22;" type="&#x22;Path | None&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_require_docker&#x22;" type="&#x22;() -> None&#x22;">
      Validate that Docker CLI is installed.

      <PySourceCode>
        ```python
        def _require_docker() -> None:
            """Validate that Docker CLI is installed."""
            if which("docker") is None:
                raise click.ClickException("docker command not found.")
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_trino_exec_base&#x22;" type="&#x22;(*, tty) -> list[str]&#x22;">
      Build the docker compose exec command for the Trino container.

      <PySourceCode>
        ```python
        def _trino_exec_base(*, tty: bool) -> list[str]:
            """Build the docker compose exec command for the Trino container."""
            phlo_dir = ensure_phlo_dir()
            project_name = get_project_name()
            cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
            cmd.append("exec")
            if not tty:
                cmd.append("-T")
            cmd.extend(["trino", "trino"])
            return cmd
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;tty&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;list[str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;trino_group&#x22;" type="&#x22;(ctx, trino_args) -> None&#x22;">
      Run the Trino shell or a Trino-specific helper command.

      <PySourceCode>
        ```python
        @click.command(
            name="trino",
            context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
        )
        @click.argument("trino_args", nargs=-1, type=click.UNPROCESSED)
        @click.pass_context
        def trino_group(ctx: click.Context, trino_args: tuple[str, ...]) -> None:
            """Run the Trino shell or a Trino-specific helper command."""
            if trino_args and trino_args[0] == "query":
                trino_query.main(
                    args=list(trino_args[1:]),
                    prog_name="phlo trino query",
                    standalone_mode=False,
                )
                return
            _require_docker()
            cmd = _trino_exec_base(tty=True)
            cmd.extend(trino_args)
            result = subprocess.run(cmd, check=False)
            if result.returncode != 0:
                raise click.ClickException(f"Trino shell exited with status {result.returncode}.")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;ctx&#x22;" type="&#x22;click.Context&#x22;" value="null" />

        <PyParameter name="&#x22;trino_args&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;trino_query&#x22;" type="&#x22;(query, query_file, catalog, schema_name, output_format, timeout_seconds) -> None&#x22;">
      Execute a SQL query against the running Trino service.

      <PySourceCode>
        ```python
        @click.command(name="query")
        @click.argument("query", required=False)
        @click.option(
            "--file",
            "query_file",
            type=click.Path(exists=True, dir_okay=False, path_type=Path),
        )
        @click.option("--catalog", default=None, help="Catalog name for the query session.")
        @click.option("--schema", "schema_name", default=None, help="Schema name for the query session.")
        @click.option("--output-format", default="CSV_HEADER_UNQUOTED", show_default=True)
        @click.option("--timeout", "timeout_seconds", default=30, show_default=True, type=int)
        def trino_query(
            query: str | None,
            query_file: Path | None,
            catalog: str | None,
            schema_name: str | None,
            output_format: str,
            timeout_seconds: int,
        ) -> None:
            """Execute a SQL query against the running Trino service."""
            _require_docker()
            sql = _read_query(query=query, file=query_file)
            cmd = _trino_exec_base(tty=False)
            if catalog:
                cmd.extend(["--catalog", catalog])
            if schema_name:
                cmd.extend(["--schema", schema_name])
            cmd.extend(["--output-format", output_format, "--execute", sql])

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
        <PyParameter name="&#x22;query&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;query_file&#x22;" type="&#x22;Path | None&#x22;" value="null" />

        <PyParameter name="&#x22;catalog&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;schema_name&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;output_format&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;timeout_seconds&#x22;" type="&#x22;int&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
