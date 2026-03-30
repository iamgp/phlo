# hooks (/docs/python-reference/packages/phlo-postgrest/phlo_postgrest/hooks)



PostgREST hooks for auto-configuration and schema discovery.

This module provides automated configuration hooks that integrate PostgREST
with Phlo's infrastructure management. It handles dynamic schema discovery
and PostgREST configuration updates based on the current database state.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_get_config_file&#x22;" type="&#x22;() -> Path&#x22;">
      Return the PostgREST configuration file path.

      Locates the PostgREST configuration within the project's .phlo directory
      at the standard location .phlo/postgrest/conf/postgrest.conf.

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        The file may not exist yet if PostgREST hasn't been initialized.
      </Callout>

      <PySourceCode>
        ```python
        def _get_config_file() -> Path:
            """Return the PostgREST configuration file path.

            Locates the PostgREST configuration within the project's .phlo directory
            at the standard location .phlo/postgrest/conf/postgrest.conf.

            Returns:
                Path: Absolute path to postgrest.conf.

            Note:
                The file may not exist yet if PostgREST hasn't been initialized.

            """
            phlo_dir = Path.cwd() / ".phlo"
            return phlo_dir / "postgrest" / "conf" / "postgrest.conf"
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;">
        Absolute path to postgrest.conf.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_read_config_values&#x22;" type="&#x22;(config_file) -> dict[str, str]&#x22;">
      Parse PostgREST configuration file into key-value pairs.

      Reads and parses the PostgREST configuration file, extracting
      configuration directives while handling comments and quoted values.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > config = \_read\_config\_values(Path("postgrest.conf"))
        > > > config.get("db-uri")
        > > > 'postgres\://user:pass\@localhost/db'
      </Callout>

      <PySourceCode>
        ```python
        def _read_config_values(config_file: Path) -> dict[str, str]:
            """Parse PostgREST configuration file into key-value pairs.

            Reads and parses the PostgREST configuration file, extracting
            configuration directives while handling comments and quoted values.

            Args:
                config_file: Path to the postgrest.conf file.

            Returns:
                dict[str, str]: Mapping of configuration keys to their values.
                Returns empty dict if file doesn't exist.

            Example:
                >>> config = _read_config_values(Path("postgrest.conf"))
                >>> config.get("db-uri")
                'postgres://user:pass@localhost/db'

            """
            values: dict[str, str] = {}
            if not config_file.exists():
                return values

            for raw_line in config_file.read_text().splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "#" in line:
                    line = line.split("#", 1)[0].strip()
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]
                values[key] = value

            return values
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;config_file&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to the postgrest.conf file.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        dict\[str, str]: Mapping of configuration keys to their values.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_parse_db_uri&#x22;" type="&#x22;(db_uri) -> dict[str, str]&#x22;">
      Parse database URI into connection components.

      Extracts username, password, and database name from a PostgreSQL
      connection URI, handling URL-encoded characters.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > \_parse\_db\_uri("postgres\://lake:secret\@localhost/lakehouse")
        > > > \{'username': 'lake', 'password': 'secret', 'database': 'lakehouse'}
      </Callout>

      <PySourceCode>
        ```python
        def _parse_db_uri(db_uri: str) -> dict[str, str]:
            """Parse database URI into connection components.

            Extracts username, password, and database name from a PostgreSQL
            connection URI, handling URL-encoded characters.

            Args:
                db_uri: PostgreSQL connection URI (e.g., 'postgres://user:pass@host/db').

            Returns:
                dict[str, str]: Dictionary with 'username', 'password', 'database' keys.

            Example:
                >>> _parse_db_uri("postgres://lake:secret@localhost/lakehouse")
                {'username': 'lake', 'password': 'secret', 'database': 'lakehouse'}

            """
            parsed = urlparse(db_uri)
            username = unquote(parsed.username or "")
            password = unquote(parsed.password or "")
            database = parsed.path.lstrip("/")
            return {
                "username": username,
                "password": password,
                "database": database,
            }
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;db_uri&#x22;" type="&#x22;str&#x22;" value="undefined">
          PostgreSQL connection URI (e.g., 'postgres\://user:pass\@host/db').
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        dict\[str, str]: Dictionary with 'username', 'password', 'database' keys.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_resolve_container_name&#x22;" type="&#x22;(service_name) -> str&#x22;">
      Resolve Docker container name using infrastructure configuration.

      Determines the actual container name based on Phlo's infrastructure
      configuration or falls back to the default naming pattern.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > \_resolve\_container\_name("postgres")
        > > > 'phlo-postgres-1'
      </Callout>

      <PySourceCode>
        ```python
        def _resolve_container_name(service_name: str) -> str:
            """Resolve Docker container name using infrastructure configuration.

            Determines the actual container name based on Phlo's infrastructure
            configuration or falls back to the default naming pattern.

            Args:
                service_name: Name of the service (e.g., 'postgres', 'postgrest').

            Returns:
                str: Resolved container name for Docker commands.

            Example:
                >>> _resolve_container_name("postgres")
                'phlo-postgres-1'

            """
            project_name = get_project_name_from_config() or Path.cwd().name
            infra = load_infrastructure_config()
            service = infra.get_service(service_name)
            if service:
                return service.get_container_name(project_name, infra.container_naming_pattern)
            return infra.container_naming_pattern.format(project=project_name, service=service_name)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Name of the service (e.g., 'postgres', 'postgrest').
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Resolved container name for Docker commands.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_discover_schemas_via_docker&#x22;" type="&#x22;(db_uri) -> list[str]&#x22;">
      Discover database schemas by querying PostgreSQL container.

      Executes psql inside the PostgreSQL Docker container to discover
      all user schemas containing tables, excluding system schemas.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > schemas = \_discover\_schemas\_via\_docker(
        > > > ...     "postgres\://lake:lakepass\@postgres/lakehouse"
        > > > ... )
        > > > print(schemas)
        > > > \['marts', 'public', 'staging']
      </Callout>

      <PySourceCode>
        ```python
        def _discover_schemas_via_docker(db_uri: str) -> list[str]:
            """Discover database schemas by querying PostgreSQL container.

            Executes psql inside the PostgreSQL Docker container to discover
            all user schemas containing tables, excluding system schemas.

            Args:
                db_uri: Database connection URI from PostgREST configuration.

            Returns:
                list[str]: Sorted list of schema names containing user tables.

            Raises:
                ValueError: If db_uri lacks username or database components.
                RuntimeError: If psql command fails or returns error.

            Example:
                >>> schemas = _discover_schemas_via_docker(
                ...     "postgres://lake:lakepass@postgres/lakehouse"
                ... )
                >>> print(schemas)
                ['marts', 'public', 'staging']

            """
            db_parts = _parse_db_uri(db_uri)
            if not db_parts["username"] or not db_parts["database"]:
                raise ValueError("db-uri must include username and database")

            sql = (
                "SELECT DISTINCT table_schema "
                "FROM information_schema.tables "
                "WHERE table_type = 'BASE TABLE' "
                "AND table_schema NOT LIKE 'pg_%' "
                "AND table_schema != 'information_schema' "
                "AND table_schema != 'hdb_catalog' "
                "ORDER BY table_schema;"
            )

            postgres_container = _resolve_container_name("postgres")
            logger.info(
                "postgrest_schema_discovery_docker_exec_started",
                postgres_container=postgres_container,
                database=db_parts["database"],
                db_user=db_parts["username"],
            )
            cmd = [
                "docker",
                "exec",
            ]
            if db_parts["password"]:
                cmd.extend(["-e", f"PGPASSWORD={db_parts['password']}"])
            cmd.extend(
                [
                    postgres_container,
                    "psql",
                    "-t",
                    "-A",
                    "-U",
                    db_parts["username"],
                    "-d",
                    db_parts["database"],
                    "-c",
                    sql,
                ]
            )

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            except Exception:
                logger.exception(
                    "postgrest_schema_discovery_docker_exec_failed",
                    postgres_container=postgres_container,
                    database=db_parts["database"],
                    db_user=db_parts["username"],
                )
                raise

            if result.returncode != 0:
                stderr_lines = [line for line in result.stderr.splitlines() if line.strip()]
                logger.error(
                    "postgrest_schema_discovery_docker_exec_failed",
                    postgres_container=postgres_container,
                    database=db_parts["database"],
                    db_user=db_parts["username"],
                    return_code=result.returncode,
                    stderr_line_count=len(stderr_lines),
                )
                raise RuntimeError(f"psql failed: {result.stderr.strip()}")

            schemas = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            logger.info(
                "postgrest_schema_discovery_docker_exec_succeeded",
                postgres_container=postgres_container,
                database=db_parts["database"],
                db_user=db_parts["username"],
                schema_count=len(schemas),
                schemas=schemas,
            )
            return schemas
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;db_uri&#x22;" type="&#x22;str&#x22;" value="undefined">
          Database connection URI from PostgREST configuration.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        list\[str]: Sorted list of schema names containing user tables.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;discover_schemas&#x22;" type="&#x22;() -> list[str]&#x22;">
      Discover all user schemas containing tables.

      Reads PostgREST configuration to obtain database connection details,
      then queries the database to find all non-system schemas with tables.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > from phlo\_postgrest.hooks import discover\_schemas
        > > > schemas = discover\_schemas()
        > > > print(schemas)
        > > > \['marts', 'public']
      </Callout>

      <PySourceCode>
        ```python
        def discover_schemas() -> list[str]:
            """Discover all user schemas containing tables.

            Reads PostgREST configuration to obtain database connection details,
            then queries the database to find all non-system schemas with tables.

            Returns:
                list[str]: Sorted list of schema names.

            Raises:
                FileNotFoundError: If PostgREST configuration file is missing.
                ValueError: If db-uri is not configured in PostgREST config.

            Example:
                >>> from phlo_postgrest.hooks import discover_schemas
                >>> schemas = discover_schemas()
                >>> print(schemas)
                ['marts', 'public']

            """
            config_file = _get_config_file()
            if not config_file.exists():
                raise FileNotFoundError(f"Config file not found at {config_file}")

            config_values = _read_config_values(config_file)
            db_uri = config_values.get("db-uri")
            if not db_uri:
                raise ValueError("db-uri not found in PostgREST config")

            return _discover_schemas_via_docker(db_uri)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list&#x22;">
        list\[str]: Sorted list of schema names.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;configure_schemas&#x22;" type="&#x22;() -> None&#x22;">
      Auto-configure PostgREST to expose all discovered schemas.

      Discovers user schemas from the database, updates the PostgREST
      configuration file with the db-schemas directive, and restarts the
      PostgREST container to apply changes.

      <Callout title="&#x22;Workflow&#x22;" type="&#x22;workflow&#x22;">
        1. Discover schemas using discover\_schemas()
        2. Prioritize 'marts' schema if present
        3. Update postgrest.conf with db-schemas value
        4. Restart PostgREST container
      </Callout>

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > from phlo\_postgrest.hooks import configure\_schemas
        > > > configure\_schemas()
        > > > Discovering user schemas for PostgREST...
        > > > Discovered schemas: marts,public,staging
        > > > Updated .phlo/postgrest/conf/postgrest.conf
        > > > PostgREST restarted successfully
      </Callout>

      <PySourceCode>
        ```python
        def configure_schemas() -> None:
            """Auto-configure PostgREST to expose all discovered schemas.

            Discovers user schemas from the database, updates the PostgREST
            configuration file with the db-schemas directive, and restarts the
            PostgREST container to apply changes.

            Workflow:
                1. Discover schemas using discover_schemas()
                2. Prioritize 'marts' schema if present
                3. Update postgrest.conf with db-schemas value
                4. Restart PostgREST container

            Raises:
                FileNotFoundError: If PostgREST configuration is missing.
                RuntimeError: If container restart fails.

            Example:
                >>> from phlo_postgrest.hooks import configure_schemas
                >>> configure_schemas()
                Discovering user schemas for PostgREST...
                Discovered schemas: marts,public,staging
                Updated .phlo/postgrest/conf/postgrest.conf
                PostgREST restarted successfully

            """
            logger.info("Discovering user schemas for PostgREST...")

            try:
                schemas = discover_schemas()
            except Exception as e:
                logger.error("Failed to discover schemas: %s", e)
                raise

            if not schemas:
                logger.warning("No user schemas found, using default 'public'")
                schemas = ["public"]
            elif "marts" in schemas:
                schemas = ["marts"] + [schema for schema in schemas if schema != "marts"]

            schemas_str = ",".join(schemas)
            logger.info("Discovered schemas: %s", schemas_str)

            # Update PostgREST config file
            config_file = _get_config_file()

            if not config_file.exists():
                logger.warning("Config file not found at %s", config_file)
                return

            # Read existing config
            content = config_file.read_text()
            lines = content.splitlines()

            # Update db-schemas line
            updated = False
            new_lines = []
            for line in lines:
                if line.startswith("db-schemas"):
                    new_lines.append(f'db-schemas = "{schemas_str}"')
                    updated = True
                else:
                    new_lines.append(line)

            if not updated:
                # Add db-schemas line after db-anon-role
                for i, line in enumerate(new_lines):
                    if line.startswith("db-anon-role"):
                        new_lines.insert(i + 1, f'db-schemas = "{schemas_str}"')
                        break

            config_file.write_text("\n".join(new_lines) + "\n")
            logger.info("Updated %s with db-schemas=%s", config_file, schemas_str)

            # Restart PostgREST container to pick up new config
            container_name = _resolve_container_name("postgrest")

            logger.info("Restarting PostgREST container to apply new schema config...")
            try:
                result = subprocess.run(
                    ["docker", "restart", container_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    logger.info("PostgREST restarted, waiting for healthy status...")
                    _wait_for_healthy(container_name, timeout=30)
                else:
                    logger.warning("Failed to restart PostgREST: %s", result.stderr)
            except Exception as e:
                logger.warning("Could not restart PostgREST container: %s", e)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_wait_for_healthy&#x22;" type="&#x22;(container_name, timeout=30) -> None&#x22;">
      Wait for a Docker container to reach healthy status.

      Polls the container's health status via Docker inspect until
      it becomes healthy or the timeout expires.

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        If container lacks healthcheck, waits briefly and returns.
        Logs warnings on timeout but does not raise exceptions.
      </Callout>

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > \_wait\_for\_healthy("phlo-postgrest-1", timeout=60)
      </Callout>

      <PySourceCode>
        ```python
        def _wait_for_healthy(container_name: str, timeout: int = 30) -> None:
            """Wait for a Docker container to reach healthy status.

            Polls the container's health status via Docker inspect until
            it becomes healthy or the timeout expires.

            Args:
                container_name: Name of the container to check.
                timeout: Maximum seconds to wait (default: 30).

            Note:
                If container lacks healthcheck, waits briefly and returns.
                Logs warnings on timeout but does not raise exceptions.

            Example:
                >>> _wait_for_healthy("phlo-postgrest-1", timeout=60)

            """
            import time

            start = time.time()
            while time.time() - start < timeout:
                try:
                    result = subprocess.run(
                        ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_name],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    status = result.stdout.strip()
                    if status == "healthy":
                        logger.info("PostgREST container is healthy")
                        return
                    if status in ("unhealthy", ""):
                        # No health check or unhealthy, just wait a bit
                        time.sleep(2)
                        logger.info("PostgREST container ready (no healthcheck)")
                        return
                except Exception:
                    pass
                time.sleep(1)
            logger.warning("Timeout waiting for PostgREST to become healthy")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;container_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Name of the container to check.
        </PyParameter>

        <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;30&#x22;">
          Maximum seconds to wait (default: 30).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
