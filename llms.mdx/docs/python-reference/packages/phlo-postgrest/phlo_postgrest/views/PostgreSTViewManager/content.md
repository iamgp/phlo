# PostgreSTViewManager (/docs/python-reference/packages/phlo-postgrest/phlo_postgrest/views/PostgreSTViewManager)



Manager for PostgreSQL view operations and database connectivity.

Handles database connections, SQL execution, view discovery, and
diff generation for PostgREST view management.

Attributes [#attributes]

<PyAttribute name="&#x22;host&#x22;" type="null" value="&#x22;host or settings.postgres_host&#x22;">
  PostgreSQL server hostname.
</PyAttribute>

<PyAttribute name="&#x22;port&#x22;" type="null" value="&#x22;int(port or settings.postgres_port)&#x22;">
  PostgreSQL server port.
</PyAttribute>

<PyAttribute name="&#x22;database&#x22;" type="null" value="&#x22;database or settings.postgres_db&#x22;">
  Database name.
</PyAttribute>

<PyAttribute name="&#x22;user&#x22;" type="null" value="&#x22;user or settings.postgres_user&#x22;">
  Database username.
</PyAttribute>

<PyAttribute name="&#x22;password&#x22;" type="null" value="&#x22;password or settings.postgres_password&#x22;">
  Database password.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, host=None, port=None, database=None, user=None, password=None)&#x22;">
  Initialize PostgreSQL connection manager with settings.

  Loads configuration from PostgrestViewsSettings for any
  parameters not explicitly provided.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > manager = PostgreSTViewManager(
    > > > ...     host="db.example.com",
    > > > ...     port=5432,
    > > > ...     database="phlo"
    > > > ... )
  </Callout>

  <PySourceCode>
    ```python
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize PostgreSQL connection manager with settings.

        Loads configuration from PostgrestViewsSettings for any
        parameters not explicitly provided.

        Args:
            host: Database server hostname.
            port: Database server port.
            database: Database name.
            user: Database username.
            password: Database password.

        Example:
            >>> manager = PostgreSTViewManager(
            ...     host="db.example.com",
            ...     port=5432,
            ...     database="phlo"
            ... )

        """
        settings = PostgrestViewsSettings()
        self.host = host or settings.postgres_host
        self.port = int(port or settings.postgres_port)
        self.database = database or settings.postgres_db
        self.user = user or settings.postgres_user
        self.password = password or settings.postgres_password
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;host&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Database server hostname.
    </PyParameter>

    <PyParameter name="&#x22;port&#x22;" type="&#x22;Optional[int]&#x22;" value="&#x22;None&#x22;">
      Database server port.
    </PyParameter>

    <PyParameter name="&#x22;database&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Database name.
    </PyParameter>

    <PyParameter name="&#x22;user&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Database username.
    </PyParameter>

    <PyParameter name="&#x22;password&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Database password.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;get_connection&#x22;" type="&#x22;(self)&#x22;">
  Establish and return a PostgreSQL database connection.

  Creates a new psycopg2 connection with autocommit enabled
  for executing DDL statements.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > conn = manager.get\_connection()
    > > > cursor = conn.cursor()
    > > > cursor.execute("SELECT 1")
  </Callout>

  <PySourceCode>
    ```python
    def get_connection(self):
        """Establish and return a PostgreSQL database connection.

        Creates a new psycopg2 connection with autocommit enabled
        for executing DDL statements.

        Returns:
            psycopg2 connection object with autocommit enabled.

        Raises:
            psycopg2.Error: If connection fails due to network or auth issues.

        Example:
            >>> conn = manager.get_connection()
            >>> cursor = conn.cursor()
            >>> cursor.execute("SELECT 1")

        """
        conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="null">
    psycopg2 connection object with autocommit enabled.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;execute_sql&#x22;" type="&#x22;(self, sql, verbose=True) -> None&#x22;">
  Execute SQL statements against the database.

  Runs the provided SQL with optional progress logging.
  Automatically manages connection lifecycle.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > manager.execute\_sql("CREATE VIEW test AS SELECT 1")
    > > > ✓ SQL executed successfully
  </Callout>

  <PySourceCode>
    ```python
    def execute_sql(self, sql: str, verbose: bool = True) -> None:
        """Execute SQL statements against the database.

        Runs the provided SQL with optional progress logging.
        Automatically manages connection lifecycle.

        Args:
            sql: SQL statement(s) to execute.
            verbose: Log execution progress if True.

        Raises:
            Exception: If SQL execution fails (re-raised after logging).

        Example:
            >>> manager.execute_sql("CREATE VIEW test AS SELECT 1")
            ✓ SQL executed successfully

        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if verbose:
                logger.info("Executing %s characters of SQL...", len(sql))
            cursor.execute(sql)
            if verbose:
                logger.info("✓ SQL executed successfully")
        except Exception as e:
            logger.error("✗ SQL execution failed: %s", e)
            raise
        finally:
            cursor.close()
            conn.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;sql&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL statement(s) to execute.
    </PyParameter>

    <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      Log execution progress if True.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_existing_views&#x22;" type="&#x22;(self, schema='api') -> set[str]&#x22;">
  Query database for existing views in a schema.

  Retrieves all view names from information\_schema.tables for
  the specified schema.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > views = manager.get\_existing\_views("api")
    > > > print(views)
    > > > \{'mrt\_orders', 'mrt\_customers'}
  </Callout>

  <PySourceCode>
    ```python
    def get_existing_views(self, schema: str = "api") -> set[str]:
        """Query database for existing views in a schema.

        Retrieves all view names from information_schema.tables for
        the specified schema.

        Args:
            schema: Schema name to query (default: 'api').

        Returns:
            set[str]: Set of existing view names in the schema.

        Example:
            >>> views = manager.get_existing_views("api")
            >>> print(views)
            {'mrt_orders', 'mrt_customers'}

        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = %s AND table_type = 'VIEW'
            """,
                (schema,),
            )
            return {row[0] for row in cursor.fetchall()}
        finally:
            cursor.close()
            conn.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="&#x22;'api'&#x22;">
      Schema name to query (default: 'api').
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;set&#x22;">
    set\[str]: Set of existing view names in the schema.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;generate_diff&#x22;" type="&#x22;(self, new_sql, schema='api') -> str&#x22;">
  Generate human-readable diff between existing and new views.

  Compares currently deployed views against newly generated SQL
  to identify created, updated, and removed views.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > diff = manager.generate\_diff(sql, "api")
    > > > print(diff)
    > > > Views to be created/updated:
    > > > mrt\_orders (updated)
    > > > mrt\_customers (new)
  </Callout>

  <PySourceCode>
    ```python
    def generate_diff(self, new_sql: str, schema: str = "api") -> str:
        """Generate human-readable diff between existing and new views.

        Compares currently deployed views against newly generated SQL
        to identify created, updated, and removed views.

        Args:
            new_sql: Generated SQL containing CREATE VIEW statements.
            schema: Schema name to compare (default: 'api').

        Returns:
            str: Formatted diff summary showing view changes.

        Example:
            >>> diff = manager.generate_diff(sql, "api")
            >>> print(diff)
            Views to be created/updated:
              mrt_orders (updated)
              mrt_customers (new)

        """
        existing_views = self.get_existing_views(schema)

        # Parse generated SQL to find new views
        import re

        new_views = set(re.findall(rf"CREATE OR REPLACE VIEW {schema}\.(\w+)", new_sql))

        lines = ["Views to be created/updated:"]
        for view in sorted(new_views):
            status = "(updated)" if view in existing_views else "(new)"
            lines.append(f"  {view} {status}")

        removed = existing_views - new_views
        if removed:
            lines.append("Views to be removed:")
            for view in sorted(removed):
                lines.append(f"  {view} (orphaned)")

        return "\n".join(lines)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;new_sql&#x22;" type="&#x22;str&#x22;" value="undefined">
      Generated SQL containing CREATE VIEW statements.
    </PyParameter>

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="&#x22;'api'&#x22;">
      Schema name to compare (default: 'api').
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Formatted diff summary showing view changes.
  </PyFunctionReturn>
</PyFunction>
