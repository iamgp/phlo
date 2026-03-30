# profile_harness (/docs/python-reference/packages/phlo-testing/phlo_testing/profile_harness)



Reusable profile-level test harnesses for real Phlo service stacks.

Provides infrastructure for integration testing against live Phlo service
stacks, including bundled stack setup, service lifecycle management, and
verification helpers.

This module enables contract tests that validate the full stack works
correctly with real services (Postgres, MinIO, Nessie, Trino, Dagster, etc.).

Example:

> > > from phlo\_testing import bootstrap\_bundled\_stack\_harness
> > > harness = bootstrap\_bundled\_stack\_harness()
> > > harness.materialize("posts", partition\_date="2024-01-01")
> > > harness.cleanup()

Key Components:

* BundledStackHarness: Runtime handle for managing a full Phlo stack
* BundledStackPorts: Service port configuration
* bootstrap\_bundled\_stack\_harness(): Factory function to create harnesses
* Service verification methods for API, observability, and lineage stacks

<PyAttribute name="&#x22;BUNDLED_STACK_CORE_SERVICES&#x22;" type="null" value="&#x22;('postgres', 'minio', 'minio-setup', 'nessie', 'trino', 'dagster', 'dagster-daemon')&#x22;" />

<PyAttribute name="&#x22;BUNDLED_STACK_DEV_PACKAGES&#x22;" type="null" value="&#x22;('phlo-alerting', 'phlo-alloy', 'phlo-dagster', 'phlo-dlt', 'phlo-dbt', 'phlo-grafana', 'phlo-iceberg', 'phlo-hasura', 'phlo-lineage', 'phlo-loki', 'phlo-minio', 'phlo-nessie', 'phlo-observatory', 'phlo-openmetadata', 'phlo-pgweb', 'phlo-postgres', 'phlo-postgrest', 'phlo-prometheus', 'phlo-superset', 'phlo-trino', 'phlo-api')&#x22;" />

<PyAttribute name="&#x22;BUNDLED_STACK_OPTIONAL_PACKAGES&#x22;" type="null" value="&#x22;('phlo-alerting', 'phlo-alloy', 'phlo-grafana', 'phlo-lineage', 'phlo-loki', 'phlo-openmetadata', 'phlo-pgweb', 'phlo-prometheus')&#x22;" />

<PyAttribute name="&#x22;BUNDLED_STACK_OPTIONAL_SERVICE_PLUGINS&#x22;" type="null" value="&#x22;('phlo-alloy', 'phlo-grafana', 'phlo-loki', 'phlo-openmetadata', 'phlo-pgweb', 'phlo-prometheus')&#x22;" />

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['BUNDLED_STACK_CORE_SERVICES', 'BUNDLED_STACK_DEV_PACKAGES', 'BundledStackHarness', 'BundledStackPorts', 'bootstrap_bundled_stack_harness', 'build_bundled_stack_env_updates', 'bundled_stack_contract_enabled', 'default_bundled_stack_project_dir', 'keep_bundled_stack_running']&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;BundledStackPorts&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/profile_harness/BundledStackPorts&#x22;" />

      <Card title="&#x22;BundledStackHarness&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/profile_harness/BundledStackHarness&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_repo_root&#x22;" type="&#x22;() -> Path&#x22;">
      Return the repository root directory.

      <PySourceCode>
        ```python
        def _repo_root() -> Path:
            """Return the repository root directory.

            Returns:
                Path to the repository root.

            """
            return Path(__file__).resolve().parents[4]
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;">
        Path to the repository root.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_load_golden_path_module&#x22;" type="&#x22;() -> Any&#x22;">
      Load the golden path module from scripts directory.

      <PySourceCode>
        ```python
        def _load_golden_path_module() -> Any:
            """Load the golden path module from scripts directory.

            Returns:
                The loaded golden path module.

            Raises:
                RuntimeError: If the module cannot be loaded.

            """
            global _GOLDEN_PATH_MODULE
            if _GOLDEN_PATH_MODULE is not None:
                return _GOLDEN_PATH_MODULE

            module_path = _repo_root() / "scripts" / "run_golden_path.py"
            spec = importlib.util.spec_from_file_location("phlo_testing_run_golden_path", module_path)
            if spec is None or spec.loader is None:
                raise RuntimeError(f"Unable to load golden-path utilities from {module_path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _GOLDEN_PATH_MODULE = module
            return module
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;">
        The loaded golden path module.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_repo_python_executable&#x22;" type="&#x22;() -> Path&#x22;">
      Return the Python executable for the repository.

      <PySourceCode>
        ```python
        def _repo_python_executable() -> Path:
            """Return the Python executable for the repository.

            Returns:
                Path to the Python executable, preferring the repo's .venv.

            """
            repo_python = _repo_root() / ".venv" / "bin" / "python"
            if repo_python.exists():
                return repo_python
            return Path(sys.executable)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;">
        Path to the Python executable, preferring the repo's .venv.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_repo_pythonpath&#x22;" type="&#x22;() -> str&#x22;">
      Build PYTHONPATH for repository execution.

      <PySourceCode>
        ```python
        def _repo_pythonpath() -> str:
            """Build PYTHONPATH for repository execution.

            Returns:
                PYTHONPATH string including repo src and packages.

            """
            repo_root = _repo_root()
            entries = [repo_root / "src", *(repo_root / "packages").glob("*/src")]
            rendered = os.pathsep.join(str(path) for path in entries)
            existing = os.environ.get("PYTHONPATH", "")
            if existing:
                return f"{rendered}{os.pathsep}{existing}"
            return rendered
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str&#x22;">
        PYTHONPATH string including repo src and packages.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_run_repo_phlo&#x22;" type="&#x22;(args, *, cwd, timeout, stream_output) -> subprocess.CompletedProcess[str]&#x22;">
      Execute phlo CLI command in the repository context.

      <PySourceCode>
        ```python
        def _run_repo_phlo(
            args: list[str],
            *,
            cwd: Path,
            timeout: int | None,
            stream_output: bool,
        ) -> subprocess.CompletedProcess[str]:
            """Execute phlo CLI command in the repository context.

            Args:
                args: Command line arguments for phlo CLI.
                cwd: Working directory for command execution.
                timeout: Maximum time to wait for command completion (seconds).
                stream_output: If True, stream output in real-time; otherwise capture.

            Returns:
                CompletedProcess with command results.

            Raises:
                RuntimeError: If the command fails (non-zero exit code).

            """
            command = [str(_repo_python_executable()), "-m", "phlo.cli.main", *args]
            env = {**os.environ, "PYTHONPATH": _repo_pythonpath()}

            if stream_output:
                process = subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                output_lines: list[str] = []
                try:
                    if process.stdout is not None:
                        for line in process.stdout:
                            print(f"    {line}", end="")
                            output_lines.append(line)
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    process.kill()
                    raise
                result = subprocess.CompletedProcess(
                    args=command,
                    returncode=process.returncode,
                    stdout="".join(output_lines),
                    stderr="",
                )
            else:
                result = subprocess.run(
                    command,
                    cwd=cwd,
                    env=env,
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                )

            if result.returncode != 0:
                raise RuntimeError(f"Command failed: {' '.join(command)}")
            return result
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;args&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
          Command line arguments for phlo CLI.
        </PyParameter>

        <PyParameter name="&#x22;cwd&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Working directory for command execution.
        </PyParameter>

        <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int | None&#x22;" value="undefined">
          Maximum time to wait for command completion (seconds).
        </PyParameter>

        <PyParameter name="&#x22;stream_output&#x22;" type="&#x22;bool&#x22;" value="undefined">
          If True, stream output in real-time; otherwise capture.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;subprocess.CompletedProcess&#x22;">
        CompletedProcess with command results.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;bundled_stack_contract_enabled&#x22;" type="&#x22;() -> bool&#x22;">
      Check if bundled stack contract tests are enabled.

      <PySourceCode>
        ```python
        def bundled_stack_contract_enabled() -> bool:
            """Check if bundled stack contract tests are enabled.

            Returns:
                True if PHLO_RUN_BUNDLED_STACK_CONTRACT is set to a truthy value.

            """
            value = os.environ.get("PHLO_RUN_BUNDLED_STACK_CONTRACT", "")
            return value.strip().lower() in {"1", "true", "yes", "on"}
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if PHLO\_RUN\_BUNDLED\_STACK\_CONTRACT is set to a truthy value.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;keep_bundled_stack_running&#x22;" type="&#x22;() -> bool&#x22;">
      Check if bundled stack should be kept running after tests.

      <PySourceCode>
        ```python
        def keep_bundled_stack_running() -> bool:
            """Check if bundled stack should be kept running after tests.

            Returns:
                True if PHLO_KEEP_BUNDLED_STACK is set to a truthy value.

            """
            value = os.environ.get("PHLO_KEEP_BUNDLED_STACK", "")
            return value.strip().lower() in {"1", "true", "yes", "on"}
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if PHLO\_KEEP\_BUNDLED\_STACK is set to a truthy value.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;default_bundled_stack_project_dir&#x22;" type="&#x22;(base_dir=None) -> Path&#x22;">
      Generate a default project directory path for bundled stack tests.

      <PySourceCode>
        ```python
        def default_bundled_stack_project_dir(base_dir: Path | None = None) -> Path:
            """Generate a default project directory path for bundled stack tests.

            Args:
                base_dir: Base directory for project creation. Defaults to .tmp in repo root.

            Returns:
                Path to a unique project directory with UUID suffix.

            """
            root = base_dir or (_repo_root() / ".tmp")
            return root / f"phlo-bundled-stack-{uuid.uuid4().hex[:8]}"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;base_dir&#x22;" type="&#x22;Path | None&#x22;" value="&#x22;None&#x22;">
          Base directory for project creation. Defaults to .tmp in repo root.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;">
        Path to a unique project directory with UUID suffix.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_cleanup_existing_bundled_stack_projects&#x22;" type="&#x22;(base_dir, *, stream_output) -> None&#x22;">
      Clean up existing bundled stack projects and Docker resources.

      Stops services and removes containers/networks from previous test runs.

      <PySourceCode>
        ```python
        def _cleanup_existing_bundled_stack_projects(base_dir: Path, *, stream_output: bool) -> None:
            """Clean up existing bundled stack projects and Docker resources.

            Stops services and removes containers/networks from previous test runs.

            Args:
                base_dir: Directory containing bundled stack projects.
                stream_output: Whether to stream command output.

            """
            utils = _load_golden_path_module()
            for project_dir in sorted(base_dir.glob("phlo-bundled-stack-*")):
                phlo_dir = project_dir / ".phlo"
                python_executable = project_dir / ".venv" / "bin" / "python"

                if phlo_dir.exists() and python_executable.exists():
                    with contextlib.suppress(Exception):
                        utils.run_phlo(
                            ["services", "stop", "--native"],
                            cwd=project_dir,
                            timeout=120,
                            check=False,
                            stream_output=stream_output,
                            python_exe=python_executable,
                        )
                    with contextlib.suppress(Exception):
                        utils.run_phlo(
                            ["services", "stop"],
                            cwd=project_dir,
                            timeout=180,
                            check=False,
                            stream_output=stream_output,
                            python_exe=python_executable,
                        )

                with contextlib.suppress(Exception):
                    utils.force_remove_directory(project_dir)

            with contextlib.suppress(Exception):
                container_result = subprocess.run(
                    ["docker", "ps", "-aq", "--filter", "name=phlo-bundled-stack-"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=30,
                )
                container_ids = [
                    line.strip() for line in container_result.stdout.splitlines() if line.strip()
                ]
                if container_ids:
                    subprocess.run(
                        ["docker", "rm", "-f", *container_ids],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=60,
                    )

            with contextlib.suppress(Exception):
                network_result = subprocess.run(
                    ["docker", "network", "ls", "--format", "{{.Name}}"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=30,
                )
                network_names = [
                    line.strip()
                    for line in network_result.stdout.splitlines()
                    if line.strip().startswith("phlo-bundled-stack-")
                ]
                if network_names:
                    subprocess.run(
                        ["docker", "network", "rm", *network_names],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=60,
                    )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;base_dir&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Directory containing bundled stack projects.
        </PyParameter>

        <PyParameter name="&#x22;stream_output&#x22;" type="&#x22;bool&#x22;" value="undefined">
          Whether to stream command output.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_port_in_use&#x22;" type="&#x22;(port) -> bool&#x22;">
      Check if a TCP port is in use.

      <PySourceCode>
        ```python
        def _port_in_use(port: int) -> bool:
            """Check if a TCP port is in use.

            Args:
                port: Port number to check.

            Returns:
                True if the port is already in use.

            """
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                return sock.connect_ex(("127.0.0.1", port)) == 0
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;port&#x22;" type="&#x22;int&#x22;" value="undefined">
          Port number to check.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if the port is already in use.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_allocate_unique_port&#x22;" type="&#x22;(service_name, default_port, *, resolve_port, used_ports) -> int&#x22;">
      Allocate a unique port for a service, avoiding conflicts.

      <PySourceCode>
        ```python
        def _allocate_unique_port(
            service_name: str,
            default_port: int,
            *,
            resolve_port: Any,
            used_ports: set[int],
        ) -> int:
            """Allocate a unique port for a service, avoiding conflicts.

            Args:
                service_name: Name of the service.
                default_port: Default port to start from.
                resolve_port: Function to resolve port (may increment).
                used_ports: Set of already allocated ports.

            Returns:
                An available port number.

            """
            candidate = int(resolve_port(service_name, default_port))
            while candidate in used_ports or _port_in_use(candidate):
                candidate += 1
            used_ports.add(candidate)
            return candidate
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Name of the service.
        </PyParameter>

        <PyParameter name="&#x22;default_port&#x22;" type="&#x22;int&#x22;" value="undefined">
          Default port to start from.
        </PyParameter>

        <PyParameter name="&#x22;resolve_port&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Function to resolve port (may increment).
        </PyParameter>

        <PyParameter name="&#x22;used_ports&#x22;" type="&#x22;set[int]&#x22;" value="undefined">
          Set of already allocated ports.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;int&#x22;">
        An available port number.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;build_bundled_stack_env_updates&#x22;" type="&#x22;(resolve_port) -> dict[str, str]&#x22;">
      Build environment variable updates for bundled stack ports.

      <PySourceCode>
        ```python
        def build_bundled_stack_env_updates(resolve_port: Any) -> dict[str, str]:
            """Build environment variable updates for bundled stack ports.

            Args:
                resolve_port: Function to resolve service ports.

            Returns:
                Dictionary of environment variable updates with unique ports.

            """
            used_ports: set[int] = set()
            updates = {
                env_key: str(
                    _allocate_unique_port(
                        service_name,
                        default_port,
                        resolve_port=resolve_port,
                        used_ports=used_ports,
                    )
                )
                for env_key, (service_name, default_port) in _BUNDLED_STACK_PORT_DEFAULTS.items()
            }
            updates["PHLO_DEV_EXTRA_PACKAGES"] = ",".join(BUNDLED_STACK_DEV_PACKAGES)
            updates["PHLO_WAP_BRANCH_CREATION_INTERVAL_SECONDS"] = "1"
            updates["PHLO_WAP_PROMOTION_INTERVAL_SECONDS"] = "1"
            return updates
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;resolve_port&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Function to resolve service ports.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary of environment variable updates with unique ports.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_verify_bind_mount_parent&#x22;" type="&#x22;(path, *, attempts=5, delay_seconds=0.5) -> None&#x22;">
      Verify Docker can read a marker file from the target parent path.

      <PySourceCode>
        ```python
        def _verify_bind_mount_parent(path: Path, *, attempts: int = 5, delay_seconds: float = 0.5) -> None:
            """Verify Docker can read a marker file from the target parent path.

            Args:
                path: Directory path to verify.
                attempts: Number of retry attempts.
                delay_seconds: Delay between attempts.

            Raises:
                RuntimeError: If Docker cannot bind-mount the directory.

            """
            target_path = path.resolve()
            target_path.mkdir(parents=True, exist_ok=True)
            marker = f".phlo_bind_check_{uuid.uuid4().hex}"
            marker_path = target_path / marker
            marker_path.write_text("ok\n")
            try:
                last_detail = "unknown bind mount error"
                for _ in range(attempts):
                    result = subprocess.run(
                        [
                            "docker",
                            "run",
                            "--rm",
                            "-v",
                            f"{target_path}:/mnt:ro",
                            "alpine:3.20",
                            "sh",
                            "-lc",
                            f"test -f /mnt/{marker}",
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=60,
                    )
                    if result.returncode == 0:
                        return
                    last_detail = (
                        result.stderr.strip() or result.stdout.strip() or "unknown bind mount error"
                    )
                    time.sleep(delay_seconds)
                raise RuntimeError(
                    "Docker cannot bind-mount the contract test project directory: "
                    f"{target_path} ({last_detail})"
                )
            finally:
                marker_path.unlink(missing_ok=True)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Directory path to verify.
        </PyParameter>

        <PyParameter name="&#x22;attempts&#x22;" type="&#x22;int&#x22;" value="&#x22;5&#x22;">
          Number of retry attempts.
        </PyParameter>

        <PyParameter name="&#x22;delay_seconds&#x22;" type="&#x22;float&#x22;" value="&#x22;0.5&#x22;">
          Delay between attempts.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_write_bundled_stack_workflow&#x22;" type="&#x22;(*, project_dir, python_executable, stream_output) -> None&#x22;">
      Write default workflow files for bundled stack testing.

      Creates sample ingestion, transformation, and publishing assets
      for testing the bundled stack.

      <PySourceCode>
        ```python
        def _write_bundled_stack_workflow(
            *,
            project_dir: Path,
            python_executable: Path,
            stream_output: bool,
        ) -> None:
            """Write default workflow files for bundled stack testing.

            Creates sample ingestion, transformation, and publishing assets
            for testing the bundled stack.

            Args:
                project_dir: Project directory path.
                python_executable: Python executable path.
                stream_output: Whether to stream command output.

            """
            utils = _load_golden_path_module()
            env_vars = cast(dict[str, str], utils.read_env_file(project_dir / ".phlo" / ".env"))

            utils.run_phlo(
                [
                    "workflow",
                    "create",
                    "--type",
                    "ingestion",
                    "--domain",
                    "jsonplaceholder",
                    "--table",
                    "posts",
                    "--unique-key",
                    "id",
                    "--cron",
                    "0 */1 * * *",
                    "--api-base-url",
                    "https://jsonplaceholder.typicode.com",
                    "--field",
                    "userId:int",
                    "--field",
                    "title:str",
                    "--field",
                    "body:str",
                ],
                cwd=project_dir,
                timeout=60,
                stream_output=stream_output,
                python_exe=python_executable,
            )

            utils.write_file(
                project_dir / "workflows" / "ingestion" / "jsonplaceholder" / "posts.py",
                '''"""Jsonplaceholder posts ingestion asset."""\n\nimport time\n\nfrom dlt.sources.rest_api import rest_api\nfrom phlo_dlt import phlo_ingestion\nfrom workflows.schemas.jsonplaceholder import RawPosts\n\n\n@phlo_ingestion(\n    table_name="posts",\n    unique_key="id",\n    validation_schema=RawPosts,\n    group="jsonplaceholder",\n    cron="0 */1 * * *",\n    freshness_hours=(1, 24),\n    validate=True,\n)\ndef posts(partition_date: str):\n    time.sleep(2)\n    base_url = "https://jsonplaceholder.typicode.com"\n    return rest_api(\n        client={"base_url": base_url},\n        resources=[{"name": "posts", "endpoint": {"path": "posts"}}],\n    )\n''',
            )

            utils.write_file(
                project_dir / "workflows" / "transforms" / "dbt" / "profiles" / "profiles.yml",
                f"""phlo:
          target: dev
          outputs:
            dev:
              type: trino
              method: none
              user: {env_vars.get("TRINO_USER", "dagster")}
              host: trino
              port: 8080
              catalog: {env_vars.get("TRINO_CATALOG", "iceberg")}
              schema: {env_vars.get("TRINO_SCHEMA", "raw")}
              http_scheme: http
              threads: 2
        """,
            )
            utils.write_file(
                project_dir / "workflows" / "transforms" / "dbt" / "models" / "sources" / "raw.yml",
                f"""version: 2\n\nsources:
          - name: raw
            database: {env_vars.get("TRINO_CATALOG", "iceberg")}
            schema: {env_vars.get("TRINO_SCHEMA", "raw")}
            tables:
              - name: posts
                columns:
                  - name: id
                  - name: user_id
                  - name: title
                  - name: body
        """,
            )
            utils.write_file(
                project_dir / "workflows" / "transforms" / "dbt" / "models" / "marts" / "posts_mart.sql",
                "{{ config(materialized='table', schema='marts') }}\nselect\n  cast(src.id as varchar) as id,\n  src.user_id,\n  src.title,\n  src.body\nfrom {{ source('raw', 'posts') }} as src\n",
            )
            utils.write_file(
                project_dir / "workflows" / "publishing" / "__init__.py",
                '"""Publishing assets."""\n',
            )
            utils.write_file(
                project_dir / "workflows" / "publishing" / "jsonplaceholder.py",
                """import dagster as dg
        import psycopg2
        from phlo_postgres.settings import get_settings
        from phlo_trino import TrinoResource
        from phlo_trino.publishing import publish_marts_to_postgres


        @dg.asset(
            name="publish_jsonplaceholder_marts",
            group_name="publishing",
            deps=[dg.AssetKey("posts_mart")],
        )
        def publish_jsonplaceholder_marts(context):
            settings = get_settings()
            trino = TrinoResource()
            postgres = psycopg2.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                user=settings.postgres_user,
                password=settings.postgres_password,
                dbname=settings.postgres_db,
            )
            try:
                return publish_marts_to_postgres(
                    context=context,
                    trino=trino,
                    postgres=postgres,
                    tables_to_publish={"posts_mart": "raw_marts.posts_mart"},
                    data_source="jsonplaceholder",
                )
            finally:
                postgres.close()
        """,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;project_dir&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Project directory path.
        </PyParameter>

        <PyParameter name="&#x22;python_executable&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Python executable path.
        </PyParameter>

        <PyParameter name="&#x22;stream_output&#x22;" type="&#x22;bool&#x22;" value="undefined">
          Whether to stream command output.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_wait_for_bundled_stack_services&#x22;" type="&#x22;(ports) -> None&#x22;">
      Wait for all bundled stack services to become ready.

      Polls Dagster, MinIO, Trino, Postgres, and Nessie until they respond.

      <PySourceCode>
        ```python
        def _wait_for_bundled_stack_services(ports: BundledStackPorts) -> None:
            """Wait for all bundled stack services to become ready.

            Polls Dagster, MinIO, Trino, Postgres, and Nessie until they respond.

            Args:
                ports: BundledStackPorts with resolved service ports.

            Raises:
                RuntimeError: If any service fails to become ready.

            """
            utils = _load_golden_path_module()
            if not utils.wait_for_tcp("127.0.0.1", ports.dagster, name="Dagster", timeout=120):
                raise RuntimeError("Dagster did not become ready")
            if not utils.wait_for_http(
                f"http://127.0.0.1:{ports.minio_api}/minio/health/live",
                name="MinIO",
                timeout=60,
            ):
                raise RuntimeError("MinIO did not become ready")
            if not utils.wait_for_http(
                f"http://127.0.0.1:{ports.trino}/v1/info",
                name="Trino",
                timeout=120,
            ):
                raise RuntimeError("Trino did not become ready")
            if not utils.wait_for_tcp("127.0.0.1", ports.postgres, name="Postgres", timeout=120):
                raise RuntimeError("Postgres did not become ready")
            if not utils.wait_for_tcp("127.0.0.1", ports.nessie, name="Nessie", timeout=120):
                raise RuntimeError("Nessie did not become ready")
            _wait_for_dagster_graphql(ports)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;ports&#x22;" type="&#x22;BundledStackPorts&#x22;" value="undefined">
          BundledStackPorts with resolved service ports.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_wait_for_dagster_graphql&#x22;" type="&#x22;(ports, *, timeout=180) -> None&#x22;">
      Wait until Dagster GraphQL is responsive.

      <PySourceCode>
        ```python
        def _wait_for_dagster_graphql(ports: BundledStackPorts, *, timeout: int = 180) -> None:
            """Wait until Dagster GraphQL is responsive.

            Args:
                ports: BundledStackPorts with resolved service ports.
                timeout: Maximum time to wait (seconds).

            Raises:
                RuntimeError: If Dagster GraphQL doesn't become ready.

            """
            deadline = time.time() + timeout
            while time.time() < deadline:
                try:
                    response = requests.post(
                        f"http://127.0.0.1:{ports.dagster}/graphql",
                        json={"query": "query Version { version }"},
                        timeout=5,
                    )
                    response.raise_for_status()
                    payload = response.json()
                    if payload.get("data", {}).get("version"):
                        return
                except Exception:
                    time.sleep(1)
                    continue
            raise RuntimeError("Dagster GraphQL did not become ready")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;ports&#x22;" type="&#x22;BundledStackPorts&#x22;" value="undefined">
          BundledStackPorts with resolved service ports.
        </PyParameter>

        <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;180&#x22;">
          Maximum time to wait (seconds).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;bootstrap_bundled_stack_harness&#x22;" type="&#x22;(*, project_dir=None, stream_output=True, keep_running=None) -> BundledStackHarness&#x22;">
      Create a real project, boot the bundled stack, and return a harness.

      This is the main entry point for bundled stack contract testing. It:

      1. Creates a temporary project directory
      2. Initializes a Phlo project
      3. Starts core services (Postgres, MinIO, Nessie, Trino, Dagster)
      4. Waits for services to be ready
      5. Returns a BundledStackHarness for test interaction

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > harness = bootstrap\_bundled\_stack\_harness()
        > > > harness.materialize("posts", partition\_date="2024-01-01")
        > > > harness.verify\_api\_stack()
        > > > harness.cleanup()
      </Callout>

      <PySourceCode>
        ```python
        def bootstrap_bundled_stack_harness(
            *,
            project_dir: Path | None = None,
            stream_output: bool = True,
            keep_running: bool | None = None,
        ) -> BundledStackHarness:
            """Create a real project, boot the bundled stack, and return a harness.

            This is the main entry point for bundled stack contract testing. It:
            1. Creates a temporary project directory
            2. Initializes a Phlo project
            3. Starts core services (Postgres, MinIO, Nessie, Trino, Dagster)
            4. Waits for services to be ready
            5. Returns a BundledStackHarness for test interaction

            Args:
                project_dir: Optional project directory path. If None, creates a temp directory.
                stream_output: Whether to stream command output during setup.
                keep_running: Whether to keep services running after tests. If None,
                    uses the PHLO_KEEP_BUNDLED_STACK environment variable.

            Returns:
                BundledStackHarness ready for testing.

            Raises:
                RuntimeError: If Docker is unavailable or setup fails.

            Example:
                >>> harness = bootstrap_bundled_stack_harness()
                >>> harness.materialize("posts", partition_date="2024-01-01")
                >>> harness.verify_api_stack()
                >>> harness.cleanup()

            """
            utils = _load_golden_path_module()
            phlo_source = _repo_root()
            target_project_dir = project_dir or default_bundled_stack_project_dir()
            should_keep_running = keep_bundled_stack_running() if keep_running is None else keep_running

            docker_info = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            if docker_info.returncode != 0:
                raise RuntimeError("Docker daemon is unavailable for bundled-stack contract tests")

            _cleanup_existing_bundled_stack_projects(target_project_dir.parent, stream_output=stream_output)
            _verify_bind_mount_parent(target_project_dir.parent)

            if target_project_dir.exists() and not utils.force_remove_directory(target_project_dir):
                raise RuntimeError(f"Unable to remove existing contract test project: {target_project_dir}")

            project_name = target_project_dir.name

            try:
                _run_repo_phlo(
                    ["init", project_name, "--template", "basic", "--force"],
                    cwd=target_project_dir.parent,
                    timeout=120,
                    stream_output=stream_output,
                )
                python_executable = Path(utils.setup_project_venv(target_project_dir, phlo_source))
                utils.run_phlo(
                    ["services", "init", "--dev", "--phlo-source", str(phlo_source), "--force"],
                    cwd=target_project_dir,
                    timeout=180,
                    stream_output=stream_output,
                    python_exe=python_executable,
                )
                utils.apply_env_updates(
                    target_project_dir / ".phlo",
                    build_bundled_stack_env_updates(utils.resolve_port),
                )
                _write_bundled_stack_workflow(
                    project_dir=target_project_dir,
                    python_executable=python_executable,
                    stream_output=stream_output,
                )
                start_args = ["services", "start"]
                for service_name in BUNDLED_STACK_CORE_SERVICES:
                    start_args.extend(["--service", service_name])
                utils.run_phlo(
                    start_args,
                    cwd=target_project_dir,
                    timeout=600,
                    stream_output=stream_output,
                    python_exe=python_executable,
                )

                env_vars = cast(dict[str, str], utils.read_env_file(target_project_dir / ".phlo" / ".env"))
                ports = BundledStackPorts.from_env(env_vars)
                _wait_for_bundled_stack_services(ports)
                return BundledStackHarness(
                    project_dir=target_project_dir,
                    phlo_source=phlo_source,
                    python_executable=python_executable,
                    ports=ports,
                    keep_running=should_keep_running,
                )
            except Exception:
                if not should_keep_running:
                    with contextlib.suppress(Exception):
                        utils.run_phlo(
                            ["services", "stop"],
                            cwd=target_project_dir,
                            timeout=300,
                            check=False,
                            stream_output=stream_output,
                            python_exe=target_project_dir / ".venv" / "bin" / "python",
                        )
                    with contextlib.suppress(Exception):
                        utils.force_remove_directory(target_project_dir)
                raise
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;project_dir&#x22;" type="&#x22;Path | None&#x22;" value="&#x22;None&#x22;">
          Optional project directory path. If None, creates a temp directory.
        </PyParameter>

        <PyParameter name="&#x22;stream_output&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Whether to stream command output during setup.
        </PyParameter>

        <PyParameter name="&#x22;keep_running&#x22;" type="&#x22;bool | None&#x22;" value="&#x22;None&#x22;">
          Whether to keep services running after tests. If None,
          uses the PHLO\_KEEP\_BUNDLED\_STACK environment variable.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_testing.profile_harness.BundledStackHarness&#x22;">
        BundledStackHarness ready for testing.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
