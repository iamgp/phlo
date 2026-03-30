# cli_plugin (/docs/python-reference/packages/phlo-dbt/phlo_dbt/cli_plugin)



CLI plugin for dbt-related commands.

This module provides the dbt CLI command group for the Phlo CLI, enabling
dbt operations like compile, run, and test to be executed either locally or
within the orchestrator container. It also handles lineage import after successful runs.

Example:

> > > Via CLI: [#via-cli]
> > >
> > > phlo dbt compile [#phlo-dbt-compile]
> > >
> > > phlo dbt run --target prod --select mrt_orders [#phlo-dbt-run---target-prod---select-mrt_orders]
> > >
> > > phlo dbt test --select tag:orders [#phlo-dbt-test---select-tagorders]
> > >
> > > Programmatically: [#programmatically]
> > >
> > > from phlo\_dbt.cli\_plugin import DbtCliPlugin
> > > plugin = DbtCliPlugin()
> > > commands = plugin.get\_cli\_commands()

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DbtCliPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/cli_plugin/DbtCliPlugin&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_container_path&#x22;" type="&#x22;(path, *, project_root) -> str&#x22;">
      Translate a project-local host path into the orchestrator container mount path.

      Converts a local filesystem path to the corresponding path inside the
      Docker container where the project is mounted (typically under /app).

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > from pathlib import Path
        > > > local = Path("workflows/transforms/dbt")
        > > > container = \_container\_path(local, project\_root=Path("."))
        > > > print(container)
        > > > /app/workflows/transforms/dbt
      </Callout>

      <PySourceCode>
        ```python
        def _container_path(path: Path, *, project_root: Path) -> str:
            """Translate a project-local host path into the orchestrator container mount path.

            Converts a local filesystem path to the corresponding path inside the
            Docker container where the project is mounted (typically under /app).

            Args:
                path: Local filesystem path to convert.
                project_root: Project root directory used as reference point.

            Returns:
                Container-mounted path as a string (e.g., "/app/workflows/transforms/dbt").

            Example:
                >>> from pathlib import Path
                >>> local = Path("workflows/transforms/dbt")
                >>> container = _container_path(local, project_root=Path("."))
                >>> print(container)
                /app/workflows/transforms/dbt

            """
            relative = path.resolve().relative_to(project_root.resolve())
            return str(Path("/app") / relative)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Local filesystem path to convert.
        </PyParameter>

        <PyParameter name="&#x22;project_root&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Project root directory used as reference point.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Container-mounted path as a string (e.g., "/app/workflows/transforms/dbt").
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_should_run_in_container&#x22;" type="&#x22;(local) -> bool&#x22;">
      Choose the default execution environment for dbt commands.

      Determines whether dbt commands should run in the orchestrator container
      or on the local host. Container execution is preferred when a Phlo
      project directory exists.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > In a project with .phlo directory [#in-a-project-with-phlo-directory]
        > > >
        > > > should\_container = \_should\_run\_in\_container(local=False)
        > > > print(should\_container)
        > > > True
        > > >
        > > > Force local execution [#force-local-execution]
        > > >
        > > > should\_local = \_should\_run\_in\_container(local=True)
        > > > print(should\_local)
        > > > False
      </Callout>

      <PySourceCode>
        ```python
        def _should_run_in_container(local: bool) -> bool:
            """Choose the default execution environment for dbt commands.

            Determines whether dbt commands should run in the orchestrator container
            or on the local host. Container execution is preferred when a Phlo
            project directory exists.

            Args:
                local: If True, force local execution regardless of environment.

            Returns:
                True if commands should run in container, False for local execution.

            Example:
                >>> # In a project with .phlo directory
                >>> should_container = _should_run_in_container(local=False)
                >>> print(should_container)
                True
                >>>
                >>> # Force local execution
                >>> should_local = _should_run_in_container(local=True)
                >>> print(should_local)
                False

            """
            if local:
                return False
            try:
                ensure_phlo_dir()
            except SystemExit:
                return False
            return True
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;local&#x22;" type="&#x22;bool&#x22;" value="undefined">
          If True, force local execution regardless of environment.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if commands should run in container, False for local execution.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_resolve_exec_service_name&#x22;" type="&#x22;() -> str&#x22;">
      Resolve the execution service from the active orchestrator adapter.

      <PySourceCode>
        ```python
        def _resolve_exec_service_name() -> str:
            """Resolve the execution service from the active orchestrator adapter."""
            from phlo.orchestrators import get_active_orchestrator

            adapter = get_active_orchestrator()
            service_name = adapter.exec_service_name()
            if not service_name:
                raise click.ClickException(
                    "The active orchestrator does not expose a container execution service. "
                    "Use --local to run dbt on the host."
                )
            return service_name
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_run_dbt_in_container&#x22;" type="&#x22;(*, subcommand, target, select_expr=None) -> None&#x22;">
      Run dbt inside the active orchestrator service container.

      <PySourceCode>
        ```python
        def _run_dbt_in_container(
            *,
            subcommand: str,
            target: str,
            select_expr: str | None = None,
        ) -> None:
            """Run dbt inside the active orchestrator service container."""
            from phlo_dbt.settings import get_settings

            logger = get_logger(f"phlo.dbt.{subcommand}")
            settings = get_settings()
            project_root = Path.cwd()
            project_dir = settings.dbt_project_path
            profiles_dir = settings.dbt_profiles_path
            exec_service_name = _resolve_exec_service_name()

            if not (project_dir / "dbt_project.yml").exists():
                click.echo(f"No dbt project found at {project_dir}", err=True)
                sys.exit(1)

            phlo_dir = ensure_phlo_dir()
            compose_cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=get_project_name())
            cmd = [*compose_cmd, "exec", "-T", exec_service_name, "dbt", subcommand]
            cmd.extend(["--project-dir", _container_path(project_dir, project_root=project_root)])
            cmd.extend(["--profiles-dir", _container_path(profiles_dir, project_root=project_root)])
            cmd.extend(["--target", target])
            if select_expr is not None:
                cmd.extend(["--select", select_expr])

            click.echo(f"Running dbt {subcommand} in {exec_service_name}...")
            logger.debug(
                f"dbt_{subcommand}_container_started",
                project_dir=str(project_dir),
                service_name=exec_service_name,
                target=target,
                select=select_expr,
            )
            try:
                result = subprocess.run(cmd, check=False)
                if result.returncode == 0:
                    _import_lineage_after_run(subcommand=subcommand, project_dir=project_dir, logger=logger)
                sys.exit(result.returncode)
            except FileNotFoundError:
                click.echo("Error: docker command not found", err=True)
                sys.exit(1)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;subcommand&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;select_expr&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_import_lineage_after_run&#x22;" type="&#x22;(*, subcommand, project_dir, logger) -> None&#x22;">
      Import manifest lineage after a successful dbt CLI run.

      <PySourceCode>
        ```python
        def _import_lineage_after_run(
            *,
            subcommand: str,
            project_dir: Path,
            logger: Any,
        ) -> None:
            """Import manifest lineage after a successful dbt CLI run."""
            if subcommand != "run":
                return

            manifest_path = project_dir / "target" / "manifest.json"
            try:
                summary = import_manifest_lineage(manifest_path)
            except Exception:
                logger.warning(
                    "dbt_cli_lineage_import_failed",
                    manifest_path=str(manifest_path),
                    exc_info=True,
                )
                return

            logger.info(
                "dbt_cli_lineage_import_succeeded",
                manifest_path=str(manifest_path),
                asset_edge_count=summary["asset_edges"],
                column_mapping_count=summary["column_mappings"],
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;subcommand&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;project_dir&#x22;" type="&#x22;Path&#x22;" value="null" />

        <PyParameter name="&#x22;logger&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_run_dbt_local&#x22;" type="&#x22;(subcommand, target, select_expr=None) -> None&#x22;">
      Run a dbt subcommand against the local project.

      <PySourceCode>
        ```python
        def _run_dbt_local(subcommand: str, target: str, select_expr: str | None = None) -> None:
            """Run a dbt subcommand against the local project.

            Args:
                subcommand: dbt subcommand to execute (compile, run, test).
                target: dbt target profile name.
                select_expr: Optional dbt model selector expression.

            """
            from phlo_dbt.settings import get_settings

            logger = get_logger(f"phlo.dbt.{subcommand}")
            settings = get_settings()
            project_dir = settings.dbt_project_path
            profiles_dir = settings.dbt_profiles_path

            if not (project_dir / "dbt_project.yml").exists():
                click.echo(f"No dbt project found at {project_dir}", err=True)
                sys.exit(1)

            ensure_dbt_profile(profiles_dir, target=target)

            cmd = [
                "dbt",
                subcommand,
                "--profiles-dir",
                str(profiles_dir),
                "--target",
                target,
            ]
            if select_expr is not None:
                cmd.extend(["--select", select_expr])

            click.echo(f"Running dbt {subcommand} at {project_dir}...")
            logger.debug(
                f"dbt_{subcommand}_started",
                project_dir=str(project_dir),
                target=target,
                select=select_expr,
            )
            try:
                result = subprocess.run(cmd, cwd=str(project_dir), check=False)
                if result.returncode == 0:
                    _import_lineage_after_run(subcommand=subcommand, project_dir=project_dir, logger=logger)
                sys.exit(result.returncode)
            except FileNotFoundError:
                click.echo("Error: dbt command not found", err=True)
                sys.exit(1)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;subcommand&#x22;" type="&#x22;str&#x22;" value="undefined">
          dbt subcommand to execute (compile, run, test).
        </PyParameter>

        <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="undefined">
          dbt target profile name.
        </PyParameter>

        <PyParameter name="&#x22;select_expr&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional dbt model selector expression.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_run_dbt&#x22;" type="&#x22;(subcommand, target, select_expr=None, *, local) -> None&#x22;">
      Run a dbt subcommand locally or inside the orchestrator container.

      <PySourceCode>
        ```python
        def _run_dbt(
            subcommand: str,
            target: str,
            select_expr: str | None = None,
            *,
            local: bool,
        ) -> None:
            """Run a dbt subcommand locally or inside the orchestrator container."""
            if _should_run_in_container(local):
                _run_dbt_in_container(subcommand=subcommand, target=target, select_expr=select_expr)
                return
            _run_dbt_local(subcommand, target, select_expr)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;subcommand&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;select_expr&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;local&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;dbt_group&#x22;" type="&#x22;() -> None&#x22;">
      Dbt commands (compile, run, test, publishing).

      <PySourceCode>
        ```python
        @click.group("dbt")
        def dbt_group() -> None:
            """Dbt commands (compile, run, test, publishing)."""
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;compile_cmd&#x22;" type="&#x22;(target, local) -> None&#x22;">
      Compile dbt models in the local project.

      <PySourceCode>
        ```python
        @dbt_group.command("compile")
        @click.option("--target", default=DEFAULT_DBT_TARGET, help="dbt target profile")
        @click.option(
            "--local", is_flag=True, help="Run dbt on the host instead of in the orchestrator container."
        )
        def compile_cmd(target: str, local: bool) -> None:
            """Compile dbt models in the local project."""
            _run_dbt("compile", target, local=local)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;local&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;run_cmd&#x22;" type="&#x22;(target, select_exprs, local) -> None&#x22;">
      Run dbt models in the local project.

      <PySourceCode>
        ```python
        @dbt_group.command("run")
        @click.option("--target", default=DEFAULT_DBT_TARGET, help="dbt target profile")
        @click.option("--select", "select_exprs", multiple=True, help="dbt model selector")
        @click.option(
            "--local", is_flag=True, help="Run dbt on the host instead of in the orchestrator container."
        )
        def run_cmd(target: str, select_exprs: tuple[str, ...], local: bool) -> None:
            """Run dbt models in the local project."""
            _run_dbt("run", target, " ".join(select_exprs) or None, local=local)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;select_exprs&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />

        <PyParameter name="&#x22;local&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;test_cmd&#x22;" type="&#x22;(target, select_exprs, local) -> None&#x22;">
      Run dbt tests in the local project.

      <PySourceCode>
        ```python
        @dbt_group.command("test")
        @click.option("--target", default=DEFAULT_DBT_TARGET, help="dbt target profile")
        @click.option("--select", "select_exprs", multiple=True, help="dbt model selector")
        @click.option(
            "--local", is_flag=True, help="Run dbt on the host instead of in the orchestrator container."
        )
        def test_cmd(target: str, select_exprs: tuple[str, ...], local: bool) -> None:
            """Run dbt tests in the local project."""
            _run_dbt("test", target, " ".join(select_exprs) or None, local=local)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;select_exprs&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />

        <PyParameter name="&#x22;local&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
