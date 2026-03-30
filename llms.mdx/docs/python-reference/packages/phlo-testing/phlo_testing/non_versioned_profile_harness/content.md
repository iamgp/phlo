# non_versioned_profile_harness (/docs/python-reference/packages/phlo-testing/phlo_testing/non_versioned_profile_harness)



Lightweight non-versioned profile harness built on DuckDB and dbt.

Provides a fast, lightweight testing harness for dbt transformations using
DuckDB as the backend. Ideal for unit testing dbt models without requiring
the full Phlo service stack.

Unlike the bundled stack harness, this uses DuckDB instead of Trino/Nessie
for faster test execution and simpler setup.

Example:

> > > from phlo\_testing import bootstrap\_non\_versioned\_profile\_harness
> > > harness = bootstrap\_non\_versioned\_profile\_harness()
> > > harness.ingest\_rows("raw\.posts", \[
> > > ...     \{"id": 1, "title": "Hello", "body": "World"}
> > > ... ])
> > > harness.run\_transform()
> > > result = harness.query("SELECT \* FROM marts.posts\_mart")
> > > harness.cleanup()

Key Components:

* NonVersionedProfileHarness: DuckDB-backed dbt test harness
* bootstrap\_non\_versioned\_profile\_harness(): Factory function

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['NonVersionedProfileHarness', 'bootstrap_non_versioned_profile_harness']&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;NonVersionedProfileHarness&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/non_versioned_profile_harness/NonVersionedProfileHarness&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_find_dbt_executable&#x22;" type="&#x22;() -> str | None&#x22;">
      Find the dbt executable in the system PATH.

      <PySourceCode>
        ```python
        def _find_dbt_executable() -> str | None:
            """Find the dbt executable in the system PATH.

            Returns:
                Path to dbt executable or None if not found.

            """
            candidate = Path(sys.executable).parent / "dbt"
            if candidate.exists():
                return str(candidate)
            return shutil.which("dbt")
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        Path to dbt executable or None if not found.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_is_missing_duckdb_adapter&#x22;" type="&#x22;(output) -> bool&#x22;">
      Check if dbt output indicates missing DuckDB adapter.

      <PySourceCode>
        ```python
        def _is_missing_duckdb_adapter(output: str) -> bool:
            """Check if dbt output indicates missing DuckDB adapter.

            Args:
                output: dbt command output to check.

            Returns:
                True if output indicates DuckDB adapter is missing.

            """
            normalized = output.lower()
            patterns = (
                "could not find adapter type duckdb",
                "adapter type duckdb is not installed",
                "no module named 'dbt.adapters.duckdb'",
                "module not found: dbt.adapters.duckdb",
                "adapter not found",
            )
            return "duckdb" in normalized and any(pattern in normalized for pattern in patterns)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;output&#x22;" type="&#x22;str&#x22;" value="undefined">
          dbt command output to check.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if output indicates DuckDB adapter is missing.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_assert_duckdb_adapter_available&#x22;" type="&#x22;(dbt_executable, project_dir) -> None&#x22;">
      Verify dbt-duckdb adapter is installed and working.

      <PySourceCode>
        ```python
        def _assert_duckdb_adapter_available(dbt_executable: str, project_dir: Path) -> None:
            """Verify dbt-duckdb adapter is installed and working.

            Args:
                dbt_executable: Path to dbt executable.
                project_dir: dbt project directory.

            Raises:
                RuntimeError: If dbt-duckdb adapter is not installed or debug fails.

            """
            env = {**os.environ, "DBT_PROFILES_DIR": str(project_dir)}
            result = subprocess.run(
                [dbt_executable, "debug", "--profiles-dir", str(project_dir)],
                cwd=project_dir,
                env=env,
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            combined_output = "\n".join((result.stdout, result.stderr))
            if _is_missing_duckdb_adapter(combined_output):
                raise RuntimeError("dbt-duckdb adapter not installed")
            if result.returncode != 0:
                raise RuntimeError(f"dbt debug failed for non-versioned harness:\n{combined_output}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dbt_executable&#x22;" type="&#x22;str&#x22;" value="undefined">
          Path to dbt executable.
        </PyParameter>

        <PyParameter name="&#x22;project_dir&#x22;" type="&#x22;Path&#x22;" value="undefined">
          dbt project directory.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;bootstrap_non_versioned_profile_harness&#x22;" type="&#x22;(*, project_dir=None) -> NonVersionedProfileHarness&#x22;">
      Create a local DuckDB-backed dbt project for non-versioned profile tests.

      Sets up a temporary dbt project with DuckDB as the backend, including
      default source and model configurations.

      <PySourceCode>
        ```python
        def bootstrap_non_versioned_profile_harness(
            *,
            project_dir: Path | None = None,
        ) -> NonVersionedProfileHarness:
            """Create a local DuckDB-backed dbt project for non-versioned profile tests.

            Sets up a temporary dbt project with DuckDB as the backend, including
            default source and model configurations.

            Args:
                project_dir: Optional project directory path. If None, creates a temp directory.

            Returns:
                NonVersionedProfileHarness ready for testing.

            Raises:
                RuntimeError: If dbt CLI is not available or dbt-duckdb adapter is missing.

            """
            target_project_dir = project_dir or Path(tempfile.mkdtemp(prefix="phlo-non-versioned-"))
            dbt_executable = _find_dbt_executable()
            if dbt_executable is None:
                raise RuntimeError("dbt CLI not available for non-versioned profile tests")

            duckdb_path = target_project_dir / "profile.duckdb"
            target_project_dir.mkdir(parents=True, exist_ok=True)

            (target_project_dir / "dbt_project.yml").write_text(
                """name: phlo_non_versioned\nversion: 1.0.0\nconfig-version: 2\nprofile: phlo_non_versioned\nmodel-paths: ["models"]\nmodels:\n  phlo_non_versioned:\n    marts:\n      +materialized: table\n"""
            )
            (target_project_dir / "profiles.yml").write_text(
                f"""phlo_non_versioned:\n  target: dev\n  outputs:\n    dev:\n      type: duckdb\n      path: {duckdb_path}\n      threads: 1\n"""
            )
            (target_project_dir / "models" / "sources").mkdir(parents=True, exist_ok=True)
            (target_project_dir / "models" / "marts").mkdir(parents=True, exist_ok=True)
            (target_project_dir / "models" / "sources" / "raw.yml").write_text(
                """version: 2\n\nsources:\n  - name: raw\n    schema: raw\n    tables:\n      - name: posts\n"""
            )
            (target_project_dir / "models" / "marts" / "posts_mart.sql").write_text(
                """{{ config(materialized='table', schema='marts') }}\nselect id, title, body from {{ source('raw', 'posts') }}\n"""
            )

            _assert_duckdb_adapter_available(dbt_executable, target_project_dir)
            return NonVersionedProfileHarness(
                project_dir=target_project_dir,
                duckdb_path=duckdb_path,
                dbt_executable=dbt_executable,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;project_dir&#x22;" type="&#x22;Path | None&#x22;" value="&#x22;None&#x22;">
          Optional project directory path. If None, creates a temp directory.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_testing.non_versioned_profile_harness.NonVersionedProfileHarness&#x22;">
        NonVersionedProfileHarness ready for testing.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
