# setup (/docs/python-reference/packages/phlo-postgrest/phlo_postgrest/setup)



PostgREST authentication infrastructure setup.

This module sets up the core PostgREST authentication infrastructure:

* PostgreSQL extensions (pgcrypto)
* Auth schema and users table
* JWT signing/verification functions
* Database roles (anon, authenticated, analyst, admin)
* Row-Level Security policies

Usage:
From CLI:
$ phlo postgrest setup-auth

From Python:

> > > from phlo\_postgrest import setup\_postgrest
> > > setup\_postgrest()

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_db_connection&#x22;" type="&#x22;(host=None, port=None, database=None, user=None, password=None)&#x22;">
      Get a PostgreSQL database connection.

      <PySourceCode>
        ```python
        def get_db_connection(
            host: Optional[str] = None,
            port: Optional[int] = None,
            database: Optional[str] = None,
            user: Optional[str] = None,
            password: Optional[str] = None,
        ):
            """Get a PostgreSQL database connection.

            Args:
                host: Database host (default: from POSTGRES_HOST env var or 'localhost')
                port: Database port (default: from POSTGRES_PORT env var or 5432)
                database: Database name (default: from POSTGRES_DB env var or 'lakehouse')
                user: Database user (default: from POSTGRES_USER env var or 'lake')
                password: Database password (default: from POSTGRES_PASSWORD env var)

            Returns:
                psycopg2 connection object

            """
            conn_params = {
                "host": host or os.getenv("POSTGRES_HOST", "localhost"),
                "port": port or int(os.getenv("POSTGRES_PORT", "5432")),
                "database": database or os.getenv("POSTGRES_DB", "lakehouse"),
                "user": user or os.getenv("POSTGRES_USER", "lake"),
                "password": password or os.getenv("POSTGRES_PASSWORD", "lakepass"),
            }

            conn = psycopg2.connect(**conn_params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            return conn
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;host&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
          Database host (default: from POSTGRES\_HOST env var or 'localhost')
        </PyParameter>

        <PyParameter name="&#x22;port&#x22;" type="&#x22;Optional[int]&#x22;" value="&#x22;None&#x22;">
          Database port (default: from POSTGRES\_PORT env var or 5432)
        </PyParameter>

        <PyParameter name="&#x22;database&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
          Database name (default: from POSTGRES\_DB env var or 'lakehouse')
        </PyParameter>

        <PyParameter name="&#x22;user&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
          Database user (default: from POSTGRES\_USER env var or 'lake')
        </PyParameter>

        <PyParameter name="&#x22;password&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
          Database password (default: from POSTGRES\_PASSWORD env var)
        </PyParameter>
      </div>

      <PyFunctionReturn type="null">
        psycopg2 connection object
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;execute_sql_file&#x22;" type="&#x22;(conn, filepath, verbose=True)&#x22;">
      Execute a SQL file.

      <PySourceCode>
        ```python
        def execute_sql_file(conn, filepath: Path, verbose: bool = True):
            """Execute a SQL file.

            Args:
                conn: Database connection
                filepath: Path to SQL file
                verbose: Print progress messages

            """
            if verbose:
                logger.info("Executing: %s", filepath.name)

            with open(filepath, "r") as f:
                sql_content = f.read()

            cursor = conn.cursor()
            try:
                cursor.execute(sql_content)
                if verbose:
                    logger.info("✓ %s completed successfully", filepath.name)
            except Exception as e:
                logger.error("✗ %s failed: %s", filepath.name, e)
                raise
            finally:
                cursor.close()
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;conn&#x22;" type="null" value="undefined">
          Database connection
        </PyParameter>

        <PyParameter name="&#x22;filepath&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to SQL file
        </PyParameter>

        <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Print progress messages
        </PyParameter>
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;check_if_setup_complete&#x22;" type="&#x22;(conn) -> bool&#x22;">
      Check if PostgREST setup has already been completed.

      <PySourceCode>
        ```python
        def check_if_setup_complete(conn) -> bool:
            """Check if PostgREST setup has already been completed.

            Returns:
                True if setup is complete, False otherwise

            """
            cursor = conn.cursor()
            try:
                # Check if auth schema exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.schemata
                        WHERE schema_name = 'auth'
                    );
                """)
                auth_exists = cursor.fetchone()[0]

                # Check if authenticator role exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_roles
                        WHERE rolname = 'authenticator'
                    );
                """)
                role_exists = cursor.fetchone()[0]

                return auth_exists and role_exists
            finally:
                cursor.close()
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;conn&#x22;" type="null" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if setup is complete, False otherwise
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;setup_postgrest&#x22;" type="&#x22;(host=None, port=None, database=None, user=None, password=None, force=False, verbose=True)&#x22;">
      Set up PostgREST authentication infrastructure.

      This function is idempotent - it's safe to run multiple times.
      It will skip setup if the infrastructure already exists unless force=True.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > from phlo\_postgrest import setup\_postgrest
        > > > setup\_postgrest()
        > > > Executing: 001\_extensions.sql
        > > > ✓ 001\_extensions.sql completed successfully
        > > > ...
        > > > ✓ PostgREST setup completed successfully!
      </Callout>

      <PySourceCode>
        ```python
        def setup_postgrest(
            host: Optional[str] = None,
            port: Optional[int] = None,
            database: Optional[str] = None,
            user: Optional[str] = None,
            password: Optional[str] = None,
            force: bool = False,
            verbose: bool = True,
        ):
            """Set up PostgREST authentication infrastructure.

            This function is idempotent - it's safe to run multiple times.
            It will skip setup if the infrastructure already exists unless force=True.

            Args:
                host: Database host
                port: Database port
                database: Database name
                user: Database user (must have superuser privileges)
                password: Database password
                force: Force re-setup even if already completed
                verbose: Print progress messages

            Example:
                >>> from phlo_postgrest import setup_postgrest
                >>> setup_postgrest()
                Executing: 001_extensions.sql
                ✓ 001_extensions.sql completed successfully
                ...
                ✓ PostgREST setup completed successfully!

            """
            if verbose:
                logger.info("=" * 50)
                logger.info("PostgREST Authentication Infrastructure Setup")
                logger.info("=" * 50)

            # Get database connection
            conn = get_db_connection(host, port, database, user, password)

            if verbose:
                cursor = conn.cursor()
                cursor.execute("SELECT current_database(), current_user;")
                db, usr = cursor.fetchone()
                logger.info("Database: %s", db)
                logger.info("User: %s", usr)
                cursor.close()
                logger.info("=" * 50)

            # Check if already setup
            if not force and check_if_setup_complete(conn):
                if verbose:
                    logger.info("✓ PostgREST infrastructure already set up.")
                    logger.info("  Use force=True to re-apply setup.")
                conn.close()
                return

            # Get SQL files directory
            sql_dir = Path(__file__).parent / "sql"

            # Execute SQL files in order
            sql_files = sorted(sql_dir.glob("*.sql"))

            for sql_file in sql_files:
                execute_sql_file(conn, sql_file, verbose)
                if verbose:
                    logger.info("")

            conn.close()

            if verbose:
                logger.info("=" * 50)
                logger.info("✓ PostgREST setup completed successfully!")
                logger.info("=" * 50)
                logger.info("Next steps:")
                logger.info("  1. Create your API views in the 'api' schema")
                logger.info("  2. Start PostgREST: docker-compose up -d postgrest")
                logger.info("  3. Test login: curl -X POST http://localhost:10018/rpc/login \\")
                logger.info("       -H 'Content-Type: application/json' \\")
                logger.info('       -d \'{"username": "analyst", "password": "<redacted>"}\'')
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;host&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
          Database host
        </PyParameter>

        <PyParameter name="&#x22;port&#x22;" type="&#x22;Optional[int]&#x22;" value="&#x22;None&#x22;">
          Database port
        </PyParameter>

        <PyParameter name="&#x22;database&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
          Database name
        </PyParameter>

        <PyParameter name="&#x22;user&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
          Database user (must have superuser privileges)
        </PyParameter>

        <PyParameter name="&#x22;password&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
          Database password
        </PyParameter>

        <PyParameter name="&#x22;force&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
          Force re-setup even if already completed
        </PyParameter>

        <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Print progress messages
        </PyParameter>
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>
</Tabs>
