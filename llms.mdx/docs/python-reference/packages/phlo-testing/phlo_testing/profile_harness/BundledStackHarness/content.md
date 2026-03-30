# BundledStackHarness (/docs/python-reference/packages/phlo-testing/phlo_testing/profile_harness/BundledStackHarness)



Runtime handle for a real bundled-stack contract environment.

Manages a full Phlo service stack for integration testing, providing
methods to start/stop services, run materializations, and verify
the health of various stack components.

Attributes [#attributes]

<PyAttribute name="&#x22;project_dir&#x22;" type="&#x22;Path&#x22;" value="null">
  Path to the temporary project directory.
</PyAttribute>

<PyAttribute name="&#x22;phlo_source&#x22;" type="&#x22;Path&#x22;" value="null">
  Path to the Phlo source repository.
</PyAttribute>

<PyAttribute name="&#x22;python_executable&#x22;" type="&#x22;Path&#x22;" value="null">
  Path to the Python executable for the project.
</PyAttribute>

<PyAttribute name="&#x22;ports&#x22;" type="&#x22;BundledStackPorts&#x22;" value="null">
  BundledStackPorts with resolved service ports.
</PyAttribute>

<PyAttribute name="&#x22;keep_running&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
  If True, keep services running after tests.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;dagster_graphql_client&#x22;" type="&#x22;(self) -> DagsterGraphQLClient&#x22;">
  Return a Dagster GraphQL client for the live harness.

  <PySourceCode>
    ```python
    def dagster_graphql_client(self) -> DagsterGraphQLClient:
        """Return a Dagster GraphQL client for the live harness.

        Returns:
            DagsterGraphQLClient configured for the harness's Dagster instance.

        """
        return DagsterGraphQLClient("127.0.0.1", port_number=self.ports.dagster)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dagster_graphql.client.client.DagsterGraphQLClient&#x22;">
    DagsterGraphQLClient configured for the harness's Dagster instance.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;run_phlo&#x22;" type="&#x22;(self, args, *, timeout=None, check=True, stream_output=True) -> subprocess.CompletedProcess[str]&#x22;">
  Execute a phlo CLI command in the harness project.

  <PySourceCode>
    ```python
    def run_phlo(
        self,
        args: list[str],
        *,
        timeout: int | None = None,
        check: bool = True,
        stream_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Execute a phlo CLI command in the harness project.

        Args:
            args: Command line arguments for phlo CLI.
            timeout: Maximum time to wait for command completion (seconds).
            check: If True, raise RuntimeError on non-zero exit code.
            stream_output: If True, stream output in real-time.

        Returns:
            CompletedProcess with command results.

        Raises:
            RuntimeError: If the command fails and check=True.

        """
        utils = _load_golden_path_module()
        return utils.run_phlo(
            args,
            cwd=self.project_dir,
            timeout=timeout,
            check=check,
            stream_output=stream_output,
            python_exe=self.python_executable,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;args&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
      Command line arguments for phlo CLI.
    </PyParameter>

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;">
      Maximum time to wait for command completion (seconds).
    </PyParameter>

    <PyParameter name="&#x22;check&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      If True, raise RuntimeError on non-zero exit code.
    </PyParameter>

    <PyParameter name="&#x22;stream_output&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      If True, stream output in real-time.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;subprocess.CompletedProcess&#x22;">
    CompletedProcess with command results.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;read_env&#x22;" type="&#x22;(self) -> dict[str, str]&#x22;">
  Read environment variables from the project's .phlo/.env file.

  <PySourceCode>
    ```python
    def read_env(self) -> dict[str, str]:
        """Read environment variables from the project's .phlo/.env file.

        Returns:
            Dictionary of environment variables.

        """
        utils = _load_golden_path_module()
        return cast(dict[str, str], utils.read_env_file(self.project_dir / ".phlo" / ".env"))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary of environment variables.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;default_partition_date&#x22;" type="&#x22;(self) -> str&#x22;">
  Return a default partition date (yesterday).

  <PySourceCode>
    ```python
    def default_partition_date(self) -> str:
        """Return a default partition date (yesterday).

        Returns:
            ISO format date string for yesterday.

        """
        return (datetime.now(UTC).date() - timedelta(days=1)).isoformat()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    ISO format date string for yesterday.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_utils&#x22;" type="&#x22;(self) -> Any&#x22;">
  Load and return the golden path utilities module.

  <PySourceCode>
    ```python
    def _utils(self) -> Any:
        """Load and return the golden path utilities module.

        Returns:
            The golden path module with utility functions.

        """
        return _load_golden_path_module()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    The golden path module with utility functions.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_temporary_env&#x22;" type="&#x22;(self, updates) -> Any&#x22;">
  Temporarily update environment variables.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > with self.\_temporary\_env(\{"KEY": "value"}):
    > > > ...     # Environment updated
    > > > ...     pass
    > > >
    > > > Environment restored [#environment-restored]
  </Callout>

  <PySourceCode>
    ```python
    @contextlib.contextmanager
    def _temporary_env(self, updates: dict[str, str | None]) -> Any:
        """Temporarily update environment variables.

        Args:
            updates: Dictionary of environment variable updates.
                Values of None will delete the variable.

        Yields:
            None

        Example:
            >>> with self._temporary_env({"KEY": "value"}):
            ...     # Environment updated
            ...     pass
            >>> # Environment restored

        """
        previous = {key: os.environ.get(key) for key in updates}
        try:
            for key, value in updates.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            yield
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;updates&#x22;" type="&#x22;dict[str, str | None]&#x22;" value="undefined">
      Dictionary of environment variable updates.
      Values of None will delete the variable.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
</PyFunction>

<PyFunction name="&#x22;install_workspace_packages&#x22;" type="&#x22;(self, package_names, *, timeout=600) -> None&#x22;">
  Install workspace packages into the harness environment.

  <PySourceCode>
    ```python
    def install_workspace_packages(
        self,
        package_names: tuple[str, ...] | list[str],
        *,
        timeout: int = 600,
    ) -> None:
        """Install workspace packages into the harness environment.

        Args:
            package_names: Names of packages to install from the workspace.
            timeout: Maximum time for installation (seconds).

        Raises:
            RuntimeError: If a package is not found in the workspace.

        """
        if not package_names:
            return

        install_args = ["uv", "pip", "install", "--python", str(self.python_executable)]
        for package_name in package_names:
            package_path = self.phlo_source / "packages" / package_name
            if not package_path.exists():
                raise RuntimeError(f"Workspace package not found: {package_name}")
            install_args.extend(["-e", str(package_path)])
        self._utils().run_command(install_args, cwd=self.project_dir, timeout=timeout)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;package_names&#x22;" type="&#x22;tuple[str, ...] | list[str]&#x22;" value="undefined">
      Names of packages to install from the workspace.
    </PyParameter>

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;600&#x22;">
      Maximum time for installation (seconds).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;ensure_full_stack_packages&#x22;" type="&#x22;(self) -> None&#x22;">
  Install all optional packages for full stack testing.

  <PySourceCode>
    ```python
    def ensure_full_stack_packages(self) -> None:
        """Install all optional packages for full stack testing."""
        self.install_workspace_packages(BUNDLED_STACK_OPTIONAL_PACKAGES)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;add_services&#x22;" type="&#x22;(self, service_names, *, timeout=180) -> None&#x22;">
  Add services to the project without starting them.

  <PySourceCode>
    ```python
    def add_services(
        self, service_names: tuple[str, ...] | list[str], *, timeout: int = 180
    ) -> None:
        """Add services to the project without starting them.

        Args:
            service_names: Names of services to add.
            timeout: Maximum time for operation (seconds).

        """
        for service_name in service_names:
            self.run_phlo(
                ["services", "add", service_name, "--no-start"],
                timeout=timeout,
                stream_output=True,
            )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;service_names&#x22;" type="&#x22;tuple[str, ...] | list[str]&#x22;" value="undefined">
      Names of services to add.
    </PyParameter>

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;180&#x22;">
      Maximum time for operation (seconds).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;start_services&#x22;" type="&#x22;(self, service_names, *, timeout=600, native=False) -> None&#x22;">
  Start specified services.

  <PySourceCode>
    ```python
    def start_services(
        self,
        service_names: tuple[str, ...] | list[str],
        *,
        timeout: int = 600,
        native: bool = False,
    ) -> None:
        """Start specified services.

        Args:
            service_names: Names of services to start.
            timeout: Maximum time for startup (seconds).
            native: If True, start native services only (no Docker).

        """
        if not service_names:
            return
        args = ["services", "start"]
        if native:
            args.append("--native")
        for service_name in service_names:
            args.extend(["--service", service_name])
        self.run_phlo(args, timeout=timeout, stream_output=True)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;service_names&#x22;" type="&#x22;tuple[str, ...] | list[str]&#x22;" value="undefined">
      Names of services to start.
    </PyParameter>

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;600&#x22;">
      Maximum time for startup (seconds).
    </PyParameter>

    <PyParameter name="&#x22;native&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
      If True, start native services only (no Docker).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;wait_for_http&#x22;" type="&#x22;(self, url, *, name, timeout=120) -> None&#x22;">
  Wait for an HTTP endpoint to become available.

  <PySourceCode>
    ```python
    def wait_for_http(self, url: str, *, name: str, timeout: int = 120) -> None:
        """Wait for an HTTP endpoint to become available.

        Args:
            url: URL to poll.
            name: Service name for error messages.
            timeout: Maximum time to wait (seconds).

        Raises:
            RuntimeError: If the endpoint doesn't become ready in time.

        """
        if not self._utils().wait_for_http(url, name=name, timeout=timeout):
            raise RuntimeError(f"{name} did not become ready: {url}")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;url&#x22;" type="&#x22;str&#x22;" value="undefined">
      URL to poll.
    </PyParameter>

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Service name for error messages.
    </PyParameter>

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;120&#x22;">
      Maximum time to wait (seconds).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;http_get&#x22;" type="&#x22;(self, url, *, headers=None, timeout=30) -> dict[str, Any] | list[Any] | str&#x22;">
  Make an HTTP GET request.

  <PySourceCode>
    ```python
    def http_get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> dict[str, Any] | list[Any] | str:
        """Make an HTTP GET request.

        Args:
            url: URL to request.
            headers: Optional request headers.
            timeout: Request timeout (seconds).

        Returns:
            Parsed JSON response or raw string.

        """
        return cast(
            dict[str, Any] | list[Any] | str,
            self._utils().http_get(url, headers=headers, timeout=timeout),
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;url&#x22;" type="&#x22;str&#x22;" value="undefined">
      URL to request.
    </PyParameter>

    <PyParameter name="&#x22;headers&#x22;" type="&#x22;dict[str, str] | None&#x22;" value="&#x22;None&#x22;">
      Optional request headers.
    </PyParameter>

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;30&#x22;">
      Request timeout (seconds).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict[str, Any] | list[Any] | str&#x22;">
    Parsed JSON response or raw string.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;http_post&#x22;" type="&#x22;(self, url, data, *, headers=None, timeout=30) -> dict[str, Any] | list[Any] | str&#x22;">
  Make an HTTP POST request.

  <PySourceCode>
    ```python
    def http_post(
        self,
        url: str,
        data: dict[str, Any] | str,
        *,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> dict[str, Any] | list[Any] | str:
        """Make an HTTP POST request.

        Args:
            url: URL to request.
            data: Request body (JSON dict or string).
            headers: Optional request headers.
            timeout: Request timeout (seconds).

        Returns:
            Parsed JSON response or raw string.

        """
        return cast(
            dict[str, Any] | list[Any] | str,
            self._utils().http_post(url, data, headers=headers, timeout=timeout),
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;url&#x22;" type="&#x22;str&#x22;" value="undefined">
      URL to request.
    </PyParameter>

    <PyParameter name="&#x22;data&#x22;" type="&#x22;dict[str, Any] | str&#x22;" value="undefined">
      Request body (JSON dict or string).
    </PyParameter>

    <PyParameter name="&#x22;headers&#x22;" type="&#x22;dict[str, str] | None&#x22;" value="&#x22;None&#x22;">
      Optional request headers.
    </PyParameter>

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;30&#x22;">
      Request timeout (seconds).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict[str, Any] | list[Any] | str&#x22;">
    Parsed JSON response or raw string.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;run_python&#x22;" type="&#x22;(self, code, *, env_updates=None, timeout=60, check=True) -> subprocess.CompletedProcess[str]&#x22;">
  Execute Python code in the harness environment.

  <PySourceCode>
    ```python
    def run_python(
        self,
        code: str,
        *,
        env_updates: dict[str, str] | None = None,
        timeout: int = 60,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Execute Python code in the harness environment.

        Args:
            code: Python code to execute.
            env_updates: Environment variable updates for execution.
            timeout: Maximum execution time (seconds).
            check: If True, raise on non-zero exit code.

        Returns:
            CompletedProcess with execution results.

        """
        env = os.environ.copy()
        if env_updates:
            env.update(env_updates)
        return subprocess.run(
            [str(self.python_executable), "-c", code],
            cwd=self.project_dir,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=check,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;code&#x22;" type="&#x22;str&#x22;" value="undefined">
      Python code to execute.
    </PyParameter>

    <PyParameter name="&#x22;env_updates&#x22;" type="&#x22;dict[str, str] | None&#x22;" value="&#x22;None&#x22;">
      Environment variable updates for execution.
    </PyParameter>

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;60&#x22;">
      Maximum execution time (seconds).
    </PyParameter>

    <PyParameter name="&#x22;check&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      If True, raise on non-zero exit code.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;subprocess.CompletedProcess&#x22;">
    CompletedProcess with execution results.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;run_command&#x22;" type="&#x22;(self, args, *, timeout=60, check=True) -> subprocess.CompletedProcess[str]&#x22;">
  Execute a shell command in the project directory.

  <PySourceCode>
    ```python
    def run_command(
        self,
        args: list[str],
        *,
        timeout: int = 60,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Execute a shell command in the project directory.

        Args:
            args: Command arguments.
            timeout: Maximum execution time (seconds).
            check: If True, raise on non-zero exit code.

        Returns:
            CompletedProcess with execution results.

        """
        return subprocess.run(
            args,
            cwd=self.project_dir,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=check,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;args&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
      Command arguments.
    </PyParameter>

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;60&#x22;">
      Maximum execution time (seconds).
    </PyParameter>

    <PyParameter name="&#x22;check&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      If True, raise on non-zero exit code.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;subprocess.CompletedProcess&#x22;">
    CompletedProcess with execution results.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;host_lineage_db_url&#x22;" type="&#x22;(self) -> str&#x22;">
  Build a PostgreSQL connection URL for the lineage database.

  <PySourceCode>
    ```python
    def host_lineage_db_url(self) -> str:
        """Build a PostgreSQL connection URL for the lineage database.

        Returns:
            PostgreSQL connection string for host access.

        """
        env_vars = self.read_env()
        return (
            "postgresql://"
            f"{env_vars.get('POSTGRES_USER', 'phlo')}:"
            f"{env_vars.get('POSTGRES_PASSWORD', 'phlo')}"
            f"@localhost:{self.ports.postgres}/{env_vars.get('POSTGRES_DB', 'phlo')}"
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    PostgreSQL connection string for host access.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;verify_default_frontends&#x22;" type="&#x22;(self) -> None&#x22;">
  Verify Phlo API and Observatory are accessible.

  Starts the services and performs health checks.

  <PySourceCode>
    ```python
    def verify_default_frontends(self) -> None:
        """Verify Phlo API and Observatory are accessible.

        Starts the services and performs health checks.

        Raises:
            RuntimeError: If services fail to start or respond.
            AssertionError: If health checks fail.

        """
        self.start_services(["phlo-api", "observatory"], timeout=600, native=True)
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.phlo_api}/health",
            name="Phlo API",
            timeout=120,
        )
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.observatory}/",
            name="Observatory",
            timeout=180,
        )
        observatory_response = requests.get(
            f"http://127.0.0.1:{self.ports.observatory}/",
            timeout=30,
        )
        observatory_response.raise_for_status()
        assert "text/html" in observatory_response.headers.get("content-type", "")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;verify_api_stack&#x22;" type="&#x22;(self) -> None&#x22;">
  Verify the API stack (Hasura, PostgREST, pgweb) is functional.

  Adds services if needed, starts them, and performs health checks
  and basic functionality tests.

  <PySourceCode>
    ```python
    def verify_api_stack(self) -> None:
        """Verify the API stack (Hasura, PostgREST, pgweb) is functional.

        Adds services if needed, starts them, and performs health checks
        and basic functionality tests.

        Raises:
            RuntimeError: If services fail to start.
            AssertionError: If health checks or API tests fail.

        """
        self.add_services(["hasura", "postgrest", "pgweb"])
        self.start_services(["hasura", "postgrest", "pgweb"], timeout=600)

        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.hasura}/healthz",
            name="Hasura",
            timeout=180,
        )
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.postgrest}/",
            name="PostgREST",
            timeout=120,
        )
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.pgweb}/",
            name="pgweb",
            timeout=120,
        )

        env_vars = self.read_env()
        hasura_secret = env_vars.get("HASURA_ADMIN_SECRET", "phlo-hasura-admin-secret")
        graphql_result = self.http_post(
            f"http://127.0.0.1:{self.ports.hasura}/v1/graphql",
            {
                "query": """
                    query {
                        marts_posts_mart(limit: 5) {
                            id
                            title
                        }
                    }
                """
            },
            headers={"x-hasura-admin-secret": hasura_secret},
        )
        assert isinstance(graphql_result, dict)
        rows = graphql_result.get("data", {}).get("marts_posts_mart")
        assert isinstance(rows, list)
        assert rows

        rest_result = self.http_get(
            f"http://127.0.0.1:{self.ports.postgrest}/posts_mart?limit=5",
            headers={"Accept": "application/json"},
        )
        assert isinstance(rest_result, list)
        assert rest_result

        pgweb_response = requests.get(f"http://127.0.0.1:{self.ports.pgweb}/", timeout=30)
        pgweb_response.raise_for_status()
        assert "pgweb" in pgweb_response.text.lower()

        backends = self.http_get(f"http://127.0.0.1:{self.ports.phlo_api}/api/backends")
        assert isinstance(backends, list)
        assert any(
            isinstance(backend, dict)
            and backend.get("name") == "hasura"
            and backend.get("healthy") is True
            for backend in backends
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;verify_observability_stack&#x22;" type="&#x22;(self) -> None&#x22;">
  Verify the observability stack (Prometheus, Loki, Alloy, Grafana).

  Adds services if needed, starts them, and performs health checks
  and basic functionality tests.

  <PySourceCode>
    ```python
    def verify_observability_stack(self) -> None:
        """Verify the observability stack (Prometheus, Loki, Alloy, Grafana).

        Adds services if needed, starts them, and performs health checks
        and basic functionality tests.

        Raises:
            RuntimeError: If services fail to start.
            AssertionError: If health checks or API tests fail.

        """
        self.add_services(["prometheus", "loki", "alloy", "grafana"])
        self.start_services(["prometheus", "loki", "alloy", "grafana"], timeout=900)

        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.prometheus}/-/healthy",
            name="Prometheus",
            timeout=180,
        )
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.loki}/ready",
            name="Loki",
            timeout=180,
        )
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.alloy}/-/ready",
            name="Alloy",
            timeout=120,
        )
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.grafana}/api/health",
            name="Grafana",
            timeout=180,
        )

        prometheus_targets = self.http_get(
            f"http://127.0.0.1:{self.ports.prometheus}/api/v1/targets"
        )
        assert isinstance(prometheus_targets, dict)
        active_targets = prometheus_targets.get("data", {}).get("activeTargets")
        assert isinstance(active_targets, list)
        assert any(
            target.get("health") == "up" for target in active_targets if isinstance(target, dict)
        )

        loki_labels = self.http_get(f"http://127.0.0.1:{self.ports.loki}/loki/api/v1/labels")
        assert isinstance(loki_labels, dict)
        assert isinstance(loki_labels.get("data"), list)

        grafana_datasources = self.http_get(
            f"http://127.0.0.1:{self.ports.grafana}/api/datasources",
            headers={"Authorization": "Basic YWRtaW46YWRtaW4="},
        )
        assert isinstance(grafana_datasources, list)
        assert grafana_datasources
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;verify_superset&#x22;" type="&#x22;(self) -> None&#x22;">
  Verify Apache Superset is functional.

  Adds the service if needed, starts it, and performs health checks.

  <PySourceCode>
    ```python
    def verify_superset(self) -> None:
        """Verify Apache Superset is functional.

        Adds the service if needed, starts it, and performs health checks.

        Raises:
            RuntimeError: If service fails to start.
            AssertionError: If health check fails.

        """
        self.add_services(["superset"])
        self.start_services(["superset"], timeout=900)
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.superset}/health",
            name="Superset",
            timeout=300,
        )
        health = self.http_get(f"http://127.0.0.1:{self.ports.superset}/health")
        if isinstance(health, dict):
            assert health.get("status") == "OK"
            return
        assert isinstance(health, str)
        assert health.strip().upper() == "OK"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;verify_metrics_cli&#x22;" type="&#x22;(self) -> None&#x22;">
  Verify the metrics CLI command works.

  Runs 'phlo metrics summary' and checks output.

  <PySourceCode>
    ```python
    def verify_metrics_cli(self) -> None:
        """Verify the metrics CLI command works.

        Runs 'phlo metrics summary' and checks output.

        Raises:
            AssertionError: If command output doesn't contain expected content.

        """
        result = self.run_phlo(
            ["metrics", "summary", "--period", "24h"],
            timeout=120,
            stream_output=False,
        )
        assert "Platform Metrics Summary" in result.stdout
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;verify_alerting_cli&#x22;" type="&#x22;(self) -> None&#x22;">
  Verify the alerting CLI command works.

  Runs 'phlo alerts list' with a mock webhook and checks output.

  <PySourceCode>
    ```python
    def verify_alerting_cli(self) -> None:
        """Verify the alerting CLI command works.

        Runs 'phlo alerts list' with a mock webhook and checks output.

        Raises:
            AssertionError: If command output doesn't contain expected content.

        """
        env_updates = {"PHLO_ALERT_SLACK_WEBHOOK": "https://example.com/mock"}
        with self._temporary_env(env_updates):
            result = self.run_phlo(
                ["alerts", "list"],
                timeout=120,
                stream_output=False,
            )
        assert "slack" in result.stdout.lower()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;emit_lineage_smoke_events&#x22;" type="&#x22;(self, *, source_asset, target_asset, metadata=None, env_updates=None) -> None&#x22;">
  Emit lineage events for smoke testing.

  <PySourceCode>
    ```python
        def emit_lineage_smoke_events(
            self,
            *,
            source_asset: str,
            target_asset: str,
            metadata: dict[str, Any] | None = None,
            env_updates: dict[str, str] | None = None,
        ) -> None:
            """Emit lineage events for smoke testing.

            Args:
                source_asset: Source asset key (e.g., "raw.posts").
                target_asset: Target asset key (e.g., "raw_marts.posts_mart").
                metadata: Optional metadata to include with the event.
                env_updates: Optional environment variable updates.

            """
            metadata_json = json.dumps(metadata or {"source": "bundled_stack_contract"})
            code = f"""
    from phlo.hooks.emitters import LineageEventContext, LineageEventEmitter

    LineageEventEmitter(LineageEventContext(tags={{"source": "bundled_stack_contract"}})).emit_edges(
        edges=[({source_asset!r}, {target_asset!r})],
        asset_keys=[{target_asset!r}],
        metadata={metadata_json},
    )
    """
            self.run_python(code, env_updates=env_updates, timeout=60)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source_asset&#x22;" type="&#x22;str&#x22;" value="undefined">
      Source asset key (e.g., "raw\.posts").
    </PyParameter>

    <PyParameter name="&#x22;target_asset&#x22;" type="&#x22;str&#x22;" value="undefined">
      Target asset key (e.g., "raw\_marts.posts\_mart").
    </PyParameter>

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Optional metadata to include with the event.
    </PyParameter>

    <PyParameter name="&#x22;env_updates&#x22;" type="&#x22;dict[str, str] | None&#x22;" value="&#x22;None&#x22;">
      Optional environment variable updates.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;verify_lineage_cli&#x22;" type="&#x22;(self) -> None&#x22;">
  Verify the lineage CLI command works.

  Emits smoke events, exports lineage, and verifies the export contains
  expected assets and edges.

  <PySourceCode>
    ```python
    def verify_lineage_cli(self) -> None:
        """Verify the lineage CLI command works.

        Emits smoke events, exports lineage, and verifies the export contains
        expected assets and edges.

        Raises:
            AssertionError: If export doesn't contain expected content.

        """
        lineage_db_url = self.host_lineage_db_url()
        self.emit_lineage_smoke_events(
            source_asset="raw.posts",
            target_asset="raw_marts.posts_mart",
            env_updates={"LINEAGE_DB_URL": lineage_db_url},
        )

        export_path = self.project_dir / ".phlo" / "lineage_contract_export.json"
        with self._temporary_env({"LINEAGE_DB_URL": lineage_db_url}):
            self.run_phlo(
                [
                    "lineage",
                    "export",
                    "raw_marts.posts_mart",
                    "--format",
                    "json",
                    "--output",
                    str(export_path),
                ],
                timeout=120,
                stream_output=False,
            )
        payload = json.loads(export_path.read_text(encoding="utf-8"))
        assert "raw.posts" in payload.get("assets", {})
        assert "raw_marts.posts_mart" in payload.get("assets", {})
        assert "raw_marts.posts_mart" in payload.get("edges", {}).get("raw.posts", [])
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;verify_openmetadata&#x22;" type="&#x22;(self) -> None&#x22;">
  Verify OpenMetadata integration works.

  Starts OpenMetadata, syncs metadata, emits events, and verifies
  the lineage and quality data appears in OpenMetadata.

  <PySourceCode>
    ```python
        def verify_openmetadata(self) -> None:
            """Verify OpenMetadata integration works.

            Starts OpenMetadata, syncs metadata, emits events, and verifies
            the lineage and quality data appears in OpenMetadata.

            Raises:
                RuntimeError: If service fails to start or sync fails.
                AssertionError: If metadata or lineage checks fail.

            """
            self.add_services(["openmetadata"])
            result = self.run_phlo(
                ["services", "start", "--service", "openmetadata"],
                timeout=1500,
                stream_output=True,
                check=False,
            )
            if result.returncode != 0:
                project_name = self.project_dir.name
                setup_container = f"{project_name}-openmetadata-setup-1"
                server_container = f"{project_name}-openmetadata-1"
                setup_result = self.run_command(
                    ["docker", "start", "-a", setup_container],
                    timeout=1500,
                    check=False,
                )
                if setup_result.returncode != 0:
                    raise RuntimeError(
                        setup_result.stdout or setup_result.stderr or "openmetadata setup failed"
                    )
                server_result = self.run_command(
                    ["docker", "start", server_container],
                    timeout=60,
                    check=False,
                )
                if server_result.returncode != 0:
                    raise RuntimeError(
                        server_result.stdout
                        or server_result.stderr
                        or "openmetadata server failed to start"
                    )
            self.wait_for_http(
                f"http://127.0.0.1:{self.ports.openmetadata}/api/v1/system/version",
                name="OpenMetadata",
                timeout=900,
            )

            env_vars = self.read_env()
            om_service = env_vars.get("OPENMETADATA_SERVICE_NAME", "phlo")
            om_database = env_vars.get(
                "OPENMETADATA_DATABASE_NAME",
                env_vars.get("TRINO_CATALOG", "iceberg"),
            )
            sync_env = {
                "OPENMETADATA_HOST": "127.0.0.1",
                "OPENMETADATA_PORT": str(self.ports.openmetadata),
                "OPENMETADATA_SERVICE_NAME": om_service,
                "OPENMETADATA_SERVICE_TYPE": env_vars.get("OPENMETADATA_SERVICE_TYPE", "Trino"),
                "OPENMETADATA_DATABASE_NAME": om_database,
                "NESSIE_HOST": "127.0.0.1",
                "NESSIE_PORT": str(self.ports.nessie),
                "TRINO_HOST": "127.0.0.1",
                "TRINO_PORT": str(self.ports.trino),
            }
            with self._temporary_env(sync_env):
                self.run_phlo(["openmetadata", "sync"], timeout=900, stream_output=False)

            om_user = env_vars.get("OPENMETADATA_USERNAME", "admin")
            om_pass = env_vars.get("OPENMETADATA_PASSWORD", "admin")
            om_base_url = f"http://127.0.0.1:{self.ports.openmetadata}"
            om_token = self._utils().openmetadata_login(
                om_base_url,
                username=om_user,
                password=om_pass,
            )
            table_fqn = f"{om_service}.{om_database}.raw_marts.posts_mart"
            source_fqn = f"{om_service}.{om_database}.raw.posts"
            table = self._utils().openmetadata_get_with_fallback(
                [f"{om_base_url}/api/v1/tables/name/{urllib.parse.quote(table_fqn, safe='')}"],
                token=om_token,
                username=om_user,
                password=om_pass,
                timeout=30,
            )
            assert isinstance(table, dict)
            assert table.get("name") == "posts_mart"

            emit_env = {
                **sync_env,
                "OPENMETADATA_USERNAME": om_user,
                "OPENMETADATA_PASSWORD": om_pass,
            }
            code = f"""
    from phlo.hooks.emitters import (
        LineageEventContext,
        LineageEventEmitter,
        QualityResultEventContext,
        QualityResultEventEmitter,
    )

    source_fqn = {source_fqn!r}
    target_fqn = {table_fqn!r}

    LineageEventEmitter(LineageEventContext(tags={{"source": "bundled_stack_contract"}})).emit_edges(
        edges=[(source_fqn, target_fqn)],
        asset_keys=[target_fqn],
        metadata={{"bundled_stack_contract": True}},
    )

    QualityResultEventEmitter(
        QualityResultEventContext(asset_key=target_fqn, tags={{"source": "bundled_stack_contract"}})
    ).emit_result(
        check_name="bundled_stack_row_count",
        passed=True,
        check_type="CountCheck",
        metadata={{"table_fqn": target_fqn, "metric_value": {{"row_count": 1}}}},
    )
    """
            self.run_python(code, env_updates=emit_env, timeout=60)
            time.sleep(2)

            lineage = self._utils().openmetadata_get_with_fallback(
                [f"{om_base_url}/api/v1/lineage/table/{table['id']}?upstreamDepth=1&downstreamDepth=0"],
                token=om_token,
                username=om_user,
                password=om_pass,
                timeout=30,
            )
            assert isinstance(lineage, dict)
            edges = lineage.get("edges") or lineage.get("upstreamEdges") or []
            assert isinstance(edges, list)
            assert edges

            test_cases = self._utils().openmetadata_get_with_fallback(
                [
                    f"{om_base_url}/api/v1/dataQuality/testCases?limit=100",
                    f"{om_base_url}/api/v1/testCases?limit=100",
                ],
                token=om_token,
                username=om_user,
                password=om_pass,
                timeout=30,
            )
            data = test_cases.get("data", []) if isinstance(test_cases, dict) else test_cases
            assert isinstance(data, list)
            assert any(
                table_fqn in str(case.get("entityLink", "")) for case in data if isinstance(case, dict)
            )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;materialize&#x22;" type="&#x22;(self, asset_name, *, partition_date=None, timeout=1200, stream_output=True) -> subprocess.CompletedProcess[str]&#x22;">
  Materialize a Dagster asset.

  <PySourceCode>
    ```python
    def materialize(
        self,
        asset_name: str,
        *,
        partition_date: str | None = None,
        timeout: int = 1200,
        stream_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Materialize a Dagster asset.

        Args:
            asset_name: Name of the asset to materialize.
            partition_date: Optional partition date for partitioned assets.
            timeout: Maximum time for materialization (seconds).
            stream_output: If True, stream output in real-time.

        Returns:
            CompletedProcess with materialization results.

        """
        args = ["materialize", asset_name]
        if partition_date is not None:
            args.extend(["--partition", partition_date])
        return self.run_phlo(args, timeout=timeout, stream_output=stream_output)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of the asset to materialize.
    </PyParameter>

    <PyParameter name="&#x22;partition_date&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional partition date for partitioned assets.
    </PyParameter>

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;1200&#x22;">
      Maximum time for materialization (seconds).
    </PyParameter>

    <PyParameter name="&#x22;stream_output&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      If True, stream output in real-time.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;subprocess.CompletedProcess&#x22;">
    CompletedProcess with materialization results.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;launch_versioned_materialization&#x22;" type="&#x22;(self, asset_name, *, partition_date=None) -> tuple[str, str]&#x22;">
  Launch a Dagster asset run tagged to an isolated WAP branch.

  Creates a temporary Nessie branch, tags the run with the branch name,
  and submits the job to Dagster.

  <PySourceCode>
    ```python
    def launch_versioned_materialization(
        self,
        asset_name: str,
        *,
        partition_date: str | None = None,
    ) -> tuple[str, str]:
        """Launch a Dagster asset run tagged to an isolated WAP branch.

        Creates a temporary Nessie branch, tags the run with the branch name,
        and submits the job to Dagster.

        Args:
            asset_name: Name of the asset to materialize.
            partition_date: Optional partition date for partitioned assets.

        Returns:
            Tuple of (run_id, branch_name).

        Raises:
            RuntimeError: If unable to create branch or launch run.

        """
        from phlo_nessie.resource import NessieResource

        branch_name = f"pipeline-run-{uuid.uuid4().hex[:12]}"
        nessie = NessieResource(base_url=f"http://127.0.0.1:{self.ports.nessie}")
        created_hash = nessie.create_branch(branch_name, from_ref="main")
        if created_hash is None:
            raise RuntimeError(f"Unable to create WAP branch {branch_name}")

        tags: dict[str, str] = {"phlo/wap_branch": branch_name}
        if partition_date:
            tags[PARTITION_NAME_TAG] = partition_date

        deadline = time.time() + 60
        last_error: Exception | None = None
        while time.time() < deadline:
            try:
                run_id = self.dagster_graphql_client().submit_job_execution(
                    job_name="__ASSET_JOB",
                    run_config={},
                    asset_selection=[asset_name],
                    tags=tags,
                )
                return run_id, branch_name
            except Exception as exc:
                last_error = exc
                time.sleep(2)
        raise RuntimeError("Unable to launch Dagster versioned materialization") from last_error
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of the asset to materialize.
    </PyParameter>

    <PyParameter name="&#x22;partition_date&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional partition date for partitioned assets.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;tuple&#x22;">
    Tuple of (run\_id, branch\_name).
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;wait_for_run_completion&#x22;" type="&#x22;(self, run_id, *, timeout=1200) -> DagsterRunStatus&#x22;">
  Poll Dagster until a launched run reaches a terminal status.

  <PySourceCode>
    ```python
    def wait_for_run_completion(self, run_id: str, *, timeout: int = 1200) -> DagsterRunStatus:
        """Poll Dagster until a launched run reaches a terminal status.

        Args:
            run_id: ID of the Dagster run to wait for.
            timeout: Maximum time to wait (seconds).

        Returns:
            Final DagsterRunStatus.

        Raises:
            RuntimeError: If run finishes with non-success status.

        """
        status = self.wait_for_run_status(
            run_id,
            expected_statuses={
                DagsterRunStatus.SUCCESS,
                DagsterRunStatus.FAILURE,
                DagsterRunStatus.CANCELED,
                DagsterRunStatus.CANCELING,
            },
            timeout=timeout,
        )
        if status != DagsterRunStatus.SUCCESS:
            raise RuntimeError(f"Dagster run {run_id} finished with status {status.value}")
        return status
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str&#x22;" value="undefined">
      ID of the Dagster run to wait for.
    </PyParameter>

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;1200&#x22;">
      Maximum time to wait (seconds).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dagster.DagsterRunStatus&#x22;">
    Final DagsterRunStatus.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;wait_for_run_status&#x22;" type="&#x22;(self, run_id, *, expected_statuses, timeout=1200) -> DagsterRunStatus&#x22;">
  Poll persisted Dagster metadata until a run reaches an expected status.

  <PySourceCode>
    ```python
    def wait_for_run_status(
        self,
        run_id: str,
        *,
        expected_statuses: set[DagsterRunStatus],
        timeout: int = 1200,
    ) -> DagsterRunStatus:
        """Poll persisted Dagster metadata until a run reaches an expected status.

        Args:
            run_id: ID of the Dagster run to wait for.
            expected_statuses: Set of statuses that indicate completion.
            timeout: Maximum time to wait (seconds).

        Returns:
            DagsterRunStatus when run reaches expected status.

        Raises:
            TimeoutError: If timeout is reached without expected status.

        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            status = self.get_run_status(run_id)
            if status in expected_statuses:
                return status
            time.sleep(1)
        raise TimeoutError(f"Timed out waiting for Dagster run {run_id}")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str&#x22;" value="undefined">
      ID of the Dagster run to wait for.
    </PyParameter>

    <PyParameter name="&#x22;expected_statuses&#x22;" type="&#x22;set[DagsterRunStatus]&#x22;" value="undefined">
      Set of statuses that indicate completion.
    </PyParameter>

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;1200&#x22;">
      Maximum time to wait (seconds).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dagster.DagsterRunStatus&#x22;">
    DagsterRunStatus when run reaches expected status.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_run_status&#x22;" type="&#x22;(self, run_id) -> DagsterRunStatus&#x22;">
  Read Dagster run status from the metadata database.

  <PySourceCode>
    ```python
    def get_run_status(self, run_id: str) -> DagsterRunStatus:
        """Read Dagster run status from the metadata database.

        Args:
            run_id: ID of the Dagster run.

        Returns:
            Current DagsterRunStatus.

        Raises:
            RuntimeError: If run is not found in database.

        """
        env_vars = self.read_env()
        connection = psycopg2.connect(
            host="127.0.0.1",
            port=self.ports.postgres,
            user=env_vars.get("POSTGRES_USER", "phlo"),
            password=env_vars.get("POSTGRES_PASSWORD", "phlo"),
            dbname=env_vars.get("POSTGRES_DB", "phlo"),
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT status FROM runs WHERE run_id = %s",
                    (run_id,),
                )
                row = cursor.fetchone()
        finally:
            connection.close()

        if row is None or row[0] is None:
            raise RuntimeError(f"Unable to find Dagster run {run_id}")
        return DagsterRunStatus(str(row[0]))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str&#x22;" value="undefined">
      ID of the Dagster run.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dagster.DagsterRunStatus&#x22;">
    Current DagsterRunStatus.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_run_tags&#x22;" type="&#x22;(self, run_id) -> dict[str, str]&#x22;">
  Read persisted Dagster run tags from the metadata database.

  <PySourceCode>
    ```python
    def get_run_tags(self, run_id: str) -> dict[str, str]:
        """Read persisted Dagster run tags from the metadata database.

        Args:
            run_id: ID of the Dagster run.

        Returns:
            Dictionary of run tags.

        """
        env_vars = self.read_env()
        connection = psycopg2.connect(
            host="127.0.0.1",
            port=self.ports.postgres,
            user=env_vars.get("POSTGRES_USER", "phlo"),
            password=env_vars.get("POSTGRES_PASSWORD", "phlo"),
            dbname=env_vars.get("POSTGRES_DB", "phlo"),
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT key, value FROM run_tags WHERE run_id = %s",
                    (run_id,),
                )
                rows = cursor.fetchall()
        finally:
            connection.close()
        return {str(key): str(value) for key, value in rows}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str&#x22;" value="undefined">
      ID of the Dagster run.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary of run tags.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;list_table_snapshots&#x22;" type="&#x22;(self, *, table_name, ref, limit=10) -> list[dict[str, Any]]&#x22;">
  List Iceberg snapshots for a table on a given ref using host-accessible settings.

  <PySourceCode>
    ```python
    def list_table_snapshots(
        self, *, table_name: str, ref: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """List Iceberg snapshots for a table on a given ref using host-accessible settings.

        Args:
            table_name: Name of the table.
            ref: Git ref or branch name.
            limit: Maximum number of snapshots to return.

        Returns:
            List of snapshot dictionaries.

        """
        from phlo_iceberg.catalog import reset_catalog_cache
        from phlo_iceberg.resource import IcebergResource
        from phlo_iceberg.settings import get_settings as get_iceberg_settings

        env_updates = {
            "ICEBERG_S3_ENDPOINT": f"http://127.0.0.1:{self.ports.minio_api}",
            "ICEBERG_NESSIE_URI": f"http://127.0.0.1:{self.ports.nessie}/iceberg",
            "AWS_ACCESS_KEY_ID": "minio",
            "AWS_SECRET_ACCESS_KEY": "minio123",
            "ICEBERG_S3_ACCESS_KEY": "minio",
            "ICEBERG_S3_SECRET_KEY": "minio123",
        }
        previous = {key: os.environ.get(key) for key in env_updates}
        try:
            for key, value in env_updates.items():
                os.environ[key] = value
            get_iceberg_settings.cache_clear()
            reset_catalog_cache()
            resource = IcebergResource(ref=ref)
            try:
                return resource.list_snapshots(table_name=table_name, limit=limit)
            except Exception:
                return []
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            get_iceberg_settings.cache_clear()
            reset_catalog_cache()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of the table.
    </PyParameter>

    <PyParameter name="&#x22;ref&#x22;" type="&#x22;str&#x22;" value="undefined">
      Git ref or branch name.
    </PyParameter>

    <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;10&#x22;">
      Maximum number of snapshots to return.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of snapshot dictionaries.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;wait_for_branch_absence&#x22;" type="&#x22;(self, branch_name, *, timeout=120) -> None&#x22;">
  Wait until a promoted WAP branch is cleaned up.

  <PySourceCode>
    ```python
    def wait_for_branch_absence(self, branch_name: str, *, timeout: int = 120) -> None:
        """Wait until a promoted WAP branch is cleaned up.

        Args:
            branch_name: Name of the branch to wait for removal.
            timeout: Maximum time to wait (seconds).

        Raises:
            TimeoutError: If branch still exists after timeout.

        """
        from phlo_nessie.resource import NessieResource

        nessie = NessieResource(base_url=f"http://127.0.0.1:{self.ports.nessie}")
        deadline = time.time() + timeout
        while time.time() < deadline:
            if not any(branch.name == branch_name for branch in nessie.list_branches()):
                return
            time.sleep(1)
        raise TimeoutError(f"Timed out waiting for branch cleanup: {branch_name}")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;branch_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of the branch to wait for removal.
    </PyParameter>

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;120&#x22;">
      Maximum time to wait (seconds).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;stop_services&#x22;" type="&#x22;(self, services=None, *, timeout=300, native=None, stream_output=True) -> None&#x22;">
  Stop services in the bundled stack.

  <PySourceCode>
    ```python
    def stop_services(
        self,
        services: list[str] | None = None,
        *,
        timeout: int = 300,
        native: bool | None = None,
        stream_output: bool = True,
    ) -> None:
        """Stop services in the bundled stack.

        Args:
            services: List of service names to stop. If None, stops all services.
            timeout: Maximum time for shutdown (seconds).
            native: If True, stop native services only. If None, stop both.
            stream_output: If True, stream output in real-time.

        """
        if services:
            args = ["services", "stop"]
            if native:
                args.append("--native")
            for service in services:
                args.extend(["--service", service])
            self.run_phlo(
                args,
                timeout=timeout,
                check=False,
                stream_output=stream_output,
            )
            return

        if native is None or native:
            with contextlib.suppress(Exception):
                self.run_phlo(
                    ["services", "stop", "--native"],
                    timeout=timeout,
                    check=False,
                    stream_output=stream_output,
                )
        if native is None or not native:
            with contextlib.suppress(Exception):
                self.run_phlo(
                    ["services", "stop"],
                    timeout=timeout,
                    check=False,
                    stream_output=stream_output,
                )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;services&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      List of service names to stop. If None, stops all services.
    </PyParameter>

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;300&#x22;">
      Maximum time for shutdown (seconds).
    </PyParameter>

    <PyParameter name="&#x22;native&#x22;" type="&#x22;bool | None&#x22;" value="&#x22;None&#x22;">
      If True, stop native services only. If None, stop both.
    </PyParameter>

    <PyParameter name="&#x22;stream_output&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      If True, stream output in real-time.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;cleanup&#x22;" type="&#x22;(self, *, stream_output=True, force=False) -> None&#x22;">
  Clean up the harness and all resources.

  Stops services and removes the project directory unless keep\_running
  is set and force is False.

  <PySourceCode>
    ```python
    def cleanup(
        self,
        *,
        stream_output: bool = True,
        force: bool = False,
    ) -> None:
        """Clean up the harness and all resources.

        Stops services and removes the project directory unless keep_running
        is set and force is False.

        Args:
            stream_output: If True, stream output during cleanup.
            force: If True, clean up even if keep_running is set.

        """
        if self.keep_running and not force:
            return
        utils = _load_golden_path_module()
        self.stop_services(stream_output=stream_output)
        with contextlib.suppress(Exception):
            utils.force_remove_directory(self.project_dir)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;stream_output&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      If True, stream output during cleanup.
    </PyParameter>

    <PyParameter name="&#x22;force&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
      If True, clean up even if keep\_running is set.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, project_dir, phlo_source, python_executable, ports, keep_running=False) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;project_dir&#x22;" type="&#x22;Path&#x22;" value="null" />

    <PyParameter name="&#x22;phlo_source&#x22;" type="&#x22;Path&#x22;" value="null" />

    <PyParameter name="&#x22;python_executable&#x22;" type="&#x22;Path&#x22;" value="null" />

    <PyParameter name="&#x22;ports&#x22;" type="&#x22;BundledStackPorts&#x22;" value="null" />

    <PyParameter name="&#x22;keep_running&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
