# cli (/docs/python-reference/packages/phlo-postgrest/phlo_postgrest/cli)



PostgREST CLI commands for Phlo.

This module defines the Click-based CLI commands for managing PostgREST,
including view generation from dbt models and authentication infrastructure
setup.

Commands:
postgrest: Main command group for PostgREST operations.
generate-views: Generate API views from dbt models.
setup-auth: Configure authentication infrastructure.

Example:
$ phlo postgrest generate-views --apply --schema api
$ phlo postgrest setup-auth --force

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;postgrest&#x22;" type="&#x22;()&#x22;">
      PostgREST API management commands.

      This command group provides operations for managing PostgREST
      configuration, including view generation and authentication setup.

      Subcommands:
      generate-views: Create API views from dbt models.
      setup-auth: Configure JWT authentication infrastructure.

      Example:
      $ phlo postgrest --help
      $ phlo postgrest generate-views --output views.sql

      <PySourceCode>
        ```python
        @click.group()
        def postgrest():
            """PostgREST API management commands.

            This command group provides operations for managing PostgREST
            configuration, including view generation and authentication setup.

            Subcommands:
                generate-views: Create API views from dbt models.
                setup-auth: Configure JWT authentication infrastructure.

            Example:
                $ phlo postgrest --help
                $ phlo postgrest generate-views --output views.sql

            """
            pass
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;generate_postgrest_views&#x22;" type="&#x22;(output, apply, diff, models, schema)&#x22;">
      Generate PostgREST API views from dbt models.

      Parses dbt manifest.json to discover models and generates CREATE VIEW
      statements that expose them through PostgREST's REST API. Can output
      to file, stdout, or apply directly to the database.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo postgrest generate-views
        $ phlo postgrest generate-views --apply --models mrt\_\*
        $ phlo postgrest generate-views --diff --output views.sql
      </Callout>

      <PySourceCode>
        ```python
        @postgrest.command(name="generate-views")
        @click.option(
            "--output",
            type=click.Path(),
            help="Output file path (default: stdout)",
        )
        @click.option(
            "--apply",
            is_flag=True,
            help="Apply views directly to database",
        )
        @click.option(
            "--diff",
            is_flag=True,
            help="Show diff of changes only",
        )
        @click.option(
            "--models",
            type=str,
            help="Filter models by pattern (e.g., mrt_*)",
        )
        @click.option(
            "--schema",
            default="api",
            help="API schema name (default: api)",
        )
        def generate_postgrest_views(
            output: Optional[str],
            apply: bool,
            diff: bool,
            models: Optional[str],
            schema: str,
        ):
            """Generate PostgREST API views from dbt models.

            Parses dbt manifest.json to discover models and generates CREATE VIEW
            statements that expose them through PostgREST's REST API. Can output
            to file, stdout, or apply directly to the database.

            Args:
                output: Path to write SQL file (default: stdout if neither apply nor
                    output specified).
                apply: If True, execute SQL directly against the database.
                diff: If True, show diff of changes without applying.
                models: Glob pattern to filter models (e.g., 'mrt_*', 'stg_*').
                schema: Target schema for API views (default: 'api').

            Raises:
                click.ClickException: If view generation or database application fails.

            Example:
                $ phlo postgrest generate-views
                $ phlo postgrest generate-views --apply --models mrt_*
                $ phlo postgrest generate-views --diff --output views.sql

            """
            logger.info(
                "postgrest_generate_views_started",
                output=output,
                apply=apply,
                diff=diff,
                model_filter=models,
                schema=schema,
            )
            try:
                result = generate_views(
                    output=output,
                    apply=apply,
                    diff=diff,
                    models=models,
                    api_schema=schema,
                    verbose=True,
                )

                if not apply and not output:
                    click.echo(result)
                logger.info(
                    "postgrest_generate_views_completed", applied=apply, output_written=bool(output)
                )

            except Exception as e:
                logger.exception("postgrest_generate_views_failed")
                raise click.ClickException(str(e))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;output&#x22;" type="&#x22;Optional[str]&#x22;" value="undefined">
          Path to write SQL file (default: stdout if neither apply nor
          output specified).
        </PyParameter>

        <PyParameter name="&#x22;apply&#x22;" type="&#x22;bool&#x22;" value="undefined">
          If True, execute SQL directly against the database.
        </PyParameter>

        <PyParameter name="&#x22;diff&#x22;" type="&#x22;bool&#x22;" value="undefined">
          If True, show diff of changes without applying.
        </PyParameter>

        <PyParameter name="&#x22;models&#x22;" type="&#x22;Optional[str]&#x22;" value="undefined">
          Glob pattern to filter models (e.g., 'mrt\_&#x2A;', 'stg\_*').
        </PyParameter>

        <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
          Target schema for API views (default: 'api').
        </PyParameter>
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;setup_postgrest_cmd&#x22;" type="&#x22;(host, port, database, user, password, force, quiet)&#x22;">
      Set up PostgREST authentication infrastructure.

      Configures the PostgreSQL database with JWT authentication functions,
      database roles (anon, authenticated, analyst, admin), user management
      tables, and Row-Level Security policies required by PostgREST.

      This command is idempotent - safe to run multiple times. It will skip
      setup if infrastructure already exists unless --force is specified.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo postgrest setup-auth
        $ phlo postgrest setup-auth --force --quiet
        $ phlo postgrest setup-auth --host db.example.com --port 5433
      </Callout>

      <PySourceCode>
        ```python
        @postgrest.command(name="setup-auth")
        @click.option("--host", help="PostgreSQL host")
        @click.option("--port", type=int, help="PostgreSQL port")
        @click.option("--database", help="PostgreSQL database name")
        @click.option("--user", help="PostgreSQL user")
        @click.option("--password", help="PostgreSQL password")
        @click.option("--force", is_flag=True, help="Force re-setup even if already exists")
        @click.option("-q", "--quiet", is_flag=True, help="Suppress output")
        def setup_postgrest_cmd(host, port, database, user, password, force, quiet):
            """Set up PostgREST authentication infrastructure.

                Configures the PostgreSQL database with JWT authentication functions,
                database roles (anon, authenticated, analyst, admin), user management
            tables, and Row-Level Security policies required by PostgREST.

                This command is idempotent - safe to run multiple times. It will skip
                setup if infrastructure already exists unless --force is specified.

            Args:
                    host: PostgreSQL server hostname (env: POSTGRES_HOST).
                    port: PostgreSQL server port (env: POSTGRES_PORT).
                    database: Database name (env: POSTGRES_DB).
                    user: Superuser username with privileges to create roles (env: POSTGRES_USER).
                    password: Database password (env: POSTGRES_PASSWORD).
                    force: Re-apply setup even if already configured.
                    quiet: Suppress progress output.

            Raises:
                    click.ClickException: If setup fails due to connection or permission errors.

            Example:
                    $ phlo postgrest setup-auth
                    $ phlo postgrest setup-auth --force --quiet
                    $ phlo postgrest setup-auth --host db.example.com --port 5433

            """
            logger.info(
                "postgrest_setup_started",
                host=host,
                port=port,
                database=database,
                user=user,
                force=force,
                quiet=quiet,
            )
            try:
                setup_postgrest(
                    host=host,
                    port=port,
                    database=database,
                    user=user,
                    password=password,
                    force=force,
                    verbose=not quiet,
                )
                logger.info("postgrest_setup_completed", force=force)
            except Exception as e:
                logger.exception("postgrest_setup_failed")
                raise click.ClickException(str(e))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;host&#x22;" type="null" value="undefined">
          PostgreSQL server hostname (env: POSTGRES\_HOST).
        </PyParameter>

        <PyParameter name="&#x22;port&#x22;" type="null" value="undefined">
          PostgreSQL server port (env: POSTGRES\_PORT).
        </PyParameter>

        <PyParameter name="&#x22;database&#x22;" type="null" value="undefined">
          Database name (env: POSTGRES\_DB).
        </PyParameter>

        <PyParameter name="&#x22;user&#x22;" type="null" value="undefined">
          Superuser username with privileges to create roles (env: POSTGRES\_USER).
        </PyParameter>

        <PyParameter name="&#x22;password&#x22;" type="null" value="undefined">
          Database password (env: POSTGRES\_PASSWORD).
        </PyParameter>

        <PyParameter name="&#x22;force&#x22;" type="null" value="undefined">
          Re-apply setup even if already configured.
        </PyParameter>

        <PyParameter name="&#x22;quiet&#x22;" type="null" value="undefined">
          Suppress progress output.
        </PyParameter>
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>
</Tabs>
