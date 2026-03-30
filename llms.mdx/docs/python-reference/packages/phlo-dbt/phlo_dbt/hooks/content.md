# hooks (/docs/python-reference/packages/phlo-dbt/phlo_dbt/hooks)



Service hooks for dbt-related setup.

This module provides lifecycle hooks for dbt compilation and setup during
Phlo service operations. It handles compiling dbt models and restarting services
to pick up manifest changes, typically used during development workflows.

Example:

> > > Run via command line [#run-via-command-line]
> > >
> > > python -m phlo_dbt.hooks compile [#python--m-phlo_dbthooks-compile]
> > >
> > > Or use in service lifecycle [#or-use-in-service-lifecycle]
> > >
> > > from phlo\_dbt.hooks import compile\_dbt
> > > exit\_code = compile\_dbt()
> > > if exit\_code == 0:
> > > ...     print("Compilation successful")

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_find_dagster_container&#x22;" type="&#x22;(project_name) -> str&#x22;">
      Resolve the Dagster webserver container via core infrastructure helpers.

      <PySourceCode>
        ```python
        def _find_dagster_container(project_name: str) -> str:
            """Resolve the Dagster webserver container via core infrastructure helpers."""
            return find_service_container(
                project_name=project_name,
                service_name="dagster",
                legacy_names=(f"{project_name}-dagster-webserver-1",),
                include_pattern=rf"{project_name}.*dagster",
                exclude_substrings=("daemon",),
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;compile_dbt&#x22;" type="&#x22;() -> int&#x22;">
      Compile dbt models in the Dagster container when a dbt project exists.

      Checks for the existence of a dbt project and, if found, compiles it within
      the Dagster webserver container. This includes:

      * Installing dbt dependencies (dbt deps)
      * Compiling models (dbt compile)
      * Restarting Dagster services to pick up the new manifest

      Designed to be called as a service hook during Phlo startup or development
      workflows.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > from phlo\_dbt.hooks import compile\_dbt
        > > > exit\_code = compile\_dbt()
        > > > if exit\_code == 0:
        > > > ...     print("dbt models compiled and Dagster restarted")
        > > > ... else:
        > > > ...     print("Warning: Compilation had issues")
      </Callout>

      <PySourceCode>
        ```python
        def compile_dbt() -> int:
            """Compile dbt models in the Dagster container when a dbt project exists.

            Checks for the existence of a dbt project and, if found, compiles it within
            the Dagster webserver container. This includes:
            - Installing dbt dependencies (dbt deps)
            - Compiling models (dbt compile)
            - Restarting Dagster services to pick up the new manifest

            Designed to be called as a service hook during Phlo startup or development
            workflows.

            Returns:
                Process-style status code (0 for success, non-zero for failure).
                Returns 0 if no dbt project exists.

            Raises:
                No explicit exceptions raised; errors are logged and reported via
                return code and print statements.

            Example:
                >>> from phlo_dbt.hooks import compile_dbt
                >>> exit_code = compile_dbt()
                >>> if exit_code == 0:
                ...     print("dbt models compiled and Dagster restarted")
                ... else:
                ...     print("Warning: Compilation had issues")

            """
            settings = get_settings()
            dbt_project_dir = Path(settings.dbt_project_dir)

            if dbt_project_dir.is_absolute():
                local_project = dbt_project_dir
                if not local_project.exists() and dbt_project_dir.parts[:2] == ("/", "app"):
                    local_project = Path.cwd() / Path(*dbt_project_dir.parts[2:])
            else:
                local_project = Path.cwd() / dbt_project_dir

            if not (local_project / "dbt_project.yml").exists():
                logger.info(
                    "dbt_hook_compile_skipped_project_missing",
                    dbt_project_path=str(local_project),
                )
                return 0

            ensure_dbt_profile(local_project / "profiles")

            logger.info(
                "dbt_hook_compile_started",
                dbt_project_path=str(local_project),
            )
            print("Compiling dbt models...")
            time.sleep(5)

            project_name = get_project_name()
            container_name = _find_dagster_container(project_name)
            logger.info(
                "dbt_hook_compile_container_resolved",
                project_name=project_name,
                container_name=container_name,
            )

            try:
                deps_result = run_command(
                    [
                        "docker",
                        "exec",
                        container_name,
                        "bash",
                        "-c",
                        f"cd {Path('/app') / dbt_project_dir} && dbt deps --profiles-dir profiles",
                    ],
                    timeout_seconds=60,
                    check=False,
                )
                if deps_result.returncode != 0:
                    logger.warning(
                        "dbt_hook_deps_failed",
                        project_name=project_name,
                        container_name=container_name,
                        returncode=deps_result.returncode,
                    )
                    print(f"Warning: dbt deps failed: {deps_result.stderr}")

                compile_result = run_command(
                    [
                        "docker",
                        "exec",
                        container_name,
                        "bash",
                        "-c",
                        f"cd {Path('/app') / dbt_project_dir} && dbt compile --profiles-dir profiles",
                    ],
                    timeout_seconds=120,
                    check=False,
                )
                if compile_result.returncode == 0:
                    logger.info(
                        "dbt_hook_compile_succeeded",
                        project_name=project_name,
                        container_name=container_name,
                    )
                    print("dbt models compiled successfully.")
                    print("Restarting Dagster to pick up dbt manifest...")
                    run_command(
                        [
                            "docker",
                            "restart",
                            container_name,
                            f"{project_name}-dagster-daemon-1",
                        ],
                        timeout_seconds=30,
                        check=False,
                    )
                else:
                    logger.warning(
                        "dbt_hook_compile_failed",
                        project_name=project_name,
                        container_name=container_name,
                        returncode=compile_result.returncode,
                    )
                    print(f"Warning: dbt compile failed: {compile_result.stderr}")
                    print("You may need to run 'dbt compile' manually.")
            except CommandError as exc:
                logger.exception(
                    "dbt_hook_compile_command_error",
                    project_name=project_name,
                    container_name=container_name,
                )
                print(f"Warning: Could not compile dbt: {exc}")
            except OSError as exc:
                logger.exception(
                    "dbt_hook_compile_os_error",
                    project_name=project_name,
                    container_name=container_name,
                )
                print(f"Warning: Could not run dbt compile: {exc}")

            logger.info(
                "dbt_hook_compile_finished",
                project_name=project_name,
                container_name=container_name,
            )
            return 0
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;int&#x22;">
        Process-style status code (0 for success, non-zero for failure).
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;main&#x22;" type="&#x22;() -> int&#x22;">
      Run dbt hook CLI entrypoint.

      <PySourceCode>
        ```python
        def main() -> int:
            """Run dbt hook CLI entrypoint.

            Returns:
                Process-style status code.

            """
            parser = argparse.ArgumentParser(description="Phlo dbt hooks")
            parser.add_argument("action", choices=["compile"])
            args = parser.parse_args()

            if args.action == "compile":
                return compile_dbt()
            return 0
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;int&#x22;">
        Process-style status code.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
