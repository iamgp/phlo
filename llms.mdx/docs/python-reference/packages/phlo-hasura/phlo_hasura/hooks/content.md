# hooks (/docs/python-reference/packages/phlo-hasura/phlo_hasura/hooks)



Hasura hooks for auto-configuration.

This module provides hook functions for automatically configuring Hasura
during project initialization or deployment. It handles environment loading
and table tracking operations.

The hooks are designed to be called from the phlo CLI or programmatically
to automate Hasura setup.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;schemas&#x22;" type="null" value="&#x22;sys.argv[2] if len(sys.argv) > 2 else 'auto'&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_load_env_files&#x22;" type="&#x22;() -> None&#x22;">
      Load environment variables from .phlo/.env and .phlo/.env.local.

      Attempts to load environment variables using python-dotenv if available,
      falling back to manual parsing if dotenv is not installed.

      <Callout title="&#x22;Files are loaded in order&#x22;" type="&#x22;files-are-loaded-in-order&#x22;">
        1. .phlo/.env
        2. .phlo/.env.local (overrides .env)
      </Callout>

      Environment variables set in .env.local take precedence over .env.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > \_load\_env\_files()

        Environment variables are now loaded from .phlo/.env files [#environment-variables-are-now-loaded-from-phloenv-files]
      </Callout>

      <PySourceCode>
        ```python
        def _load_env_files() -> None:
            """Load environment variables from .phlo/.env and .phlo/.env.local.

            Attempts to load environment variables using python-dotenv if available,
            falling back to manual parsing if dotenv is not installed.

            Files are loaded in order:
                1. .phlo/.env
                2. .phlo/.env.local (overrides .env)

            Environment variables set in .env.local take precedence over .env.

            Raises:
                No exceptions are raised; failures are silently ignored.

            Example:
                >>> _load_env_files()
                # Environment variables are now loaded from .phlo/.env files

            """
            try:
                from dotenv import load_dotenv

                phlo_dir = Path.cwd() / ".phlo"
                env_file = phlo_dir / ".env"
                env_local = phlo_dir / ".env.local"

                if env_file.exists():
                    load_dotenv(env_file)
                if env_local.exists():
                    load_dotenv(env_local, override=True)
            except ImportError:
                # dotenv not available, try manual parsing
                phlo_dir = Path.cwd() / ".phlo"
                for env_file in [phlo_dir / ".env", phlo_dir / ".env.local"]:
                    if env_file.exists():
                        with open(env_file) as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith("#") and "=" in line:
                                    key, _, value = line.partition("=")
                                    # Remove quotes if present
                                    value = value.strip().strip('"').strip("'")
                                    os.environ.setdefault(key.strip(), value)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;track_tables&#x22;" type="&#x22;(schemas='api') -> None&#x22;">
      Auto-track tables in the specified schema(s).

      Automatically discovers and tracks all tables in the specified schemas.
      Can track multiple schemas at once or auto-discover all user schemas.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > track\_tables("api")  # Track single schema
        > > > track\_tables("marts,api")  # Track multiple schemas
        > > > track\_tables("auto")  # Auto-discover all schemas
      </Callout>

      <PySourceCode>
        ```python
        def track_tables(schemas: str = "api") -> None:
            """Auto-track tables in the specified schema(s).

            Automatically discovers and tracks all tables in the specified schemas.
            Can track multiple schemas at once or auto-discover all user schemas.

            Args:
                schemas: Comma-separated list of schemas to track (e.g., "marts,api"),
                         or "auto" to discover all user schemas automatically.

            Raises:
                Exception: If auto-tracking fails (propagated from underlying operations).

            Example:
                >>> track_tables("api")  # Track single schema
                >>> track_tables("marts,api")  # Track multiple schemas
                >>> track_tables("auto")  # Auto-discover all schemas

            """
            from phlo_hasura.track import auto_track, auto_track_all

            if schemas == "auto":
                logger.info("Auto-discovering all user schemas...")
                try:
                    result = auto_track_all(verbose=True)
                    logger.info("Auto-discovery complete: %d schemas processed", len(result))
                except Exception as e:
                    logger.error("Failed to auto-track tables: %s", e)
                    raise
            else:
                schema_list = [s.strip() for s in schemas.split(",") if s.strip()]
                for schema in schema_list:
                    logger.info("Auto-tracking tables in schema: %s", schema)
                    try:
                        result = auto_track(schema=schema, verbose=True)
                        logger.info("Tracking complete for %s: %s", schema, result)
                    except Exception as e:
                        logger.error("Failed to auto-track tables in schema %s: %s", schema, e)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;schemas&#x22;" type="&#x22;str&#x22;" value="&#x22;'api'&#x22;">
          Comma-separated list of schemas to track (e.g., "marts,api"),
          or "auto" to discover all user schemas automatically.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
