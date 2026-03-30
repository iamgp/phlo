# HasuraTableTracker (/docs/python-reference/packages/phlo-hasura/phlo_hasura/track/HasuraTableTracker)



Automatically discovers and tracks PostgreSQL tables in Hasura.

Provides methods for schema discovery, table tracking, relationship
creation from foreign keys, and default permission setup.

Attributes [#attributes]

<PyAttribute name="&#x22;client&#x22;" type="null" value="&#x22;hasura_client or HasuraClient()&#x22;">
  HasuraClient for Hasura API operations.
</PyAttribute>

<PyAttribute name="&#x22;db_name&#x22;" type="null" value="&#x22;db_name or settings.postgres_db&#x22;">
  PostgreSQL database name.
</PyAttribute>

<PyAttribute name="&#x22;db_user&#x22;" type="null" value="&#x22;db_user or settings.postgres_user&#x22;">
  PostgreSQL username.
</PyAttribute>

<PyAttribute name="&#x22;db_password&#x22;" type="null" value="&#x22;db_password or settings.postgres_password&#x22;">
  PostgreSQL password.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, hasura_client=None, db_host=None, db_port=None, db_name=None, db_user=None, db_password=None)&#x22;">
  Initialize table tracker.

  The database host is automatically resolved to handle running
  outside Docker containers.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > tracker = HasuraTableTracker()
    > > > custom\_tracker = HasuraTableTracker(
    > > > ...     db\_host="localhost",
    > > > ...     db\_port=5433
    > > > ... )
  </Callout>

  <PySourceCode>
    ```python
    def __init__(
        self,
        hasura_client: HasuraClient | None = None,
        db_host: str | None = None,
        db_port: int | None = None,
        db_name: str | None = None,
        db_user: str | None = None,
        db_password: str | None = None,
    ):
        """Initialize table tracker.

        Args:
            hasura_client: HasuraClient instance for API operations.
            db_host: PostgreSQL host (default: from HasuraPostgresSettings).
            db_port: PostgreSQL port (default: from HasuraPostgresSettings).
            db_name: PostgreSQL database name (default: from HasuraPostgresSettings).
            db_user: PostgreSQL username (default: from HasuraPostgresSettings).
            db_password: PostgreSQL password (default: from HasuraPostgresSettings).

        The database host is automatically resolved to handle running
        outside Docker containers.

        Example:
            >>> tracker = HasuraTableTracker()
            >>> custom_tracker = HasuraTableTracker(
            ...     db_host="localhost",
            ...     db_port=5433
            ... )

        """
        self.client = hasura_client or HasuraClient()

        settings = HasuraPostgresSettings()
        raw_host = db_host or settings.postgres_host
        raw_port = db_port or settings.postgres_port

        # Resolve host - handle running outside Docker
        self.db_host, self.db_port = _resolve_db_host(raw_host, raw_port)
        self.db_name = db_name or settings.postgres_db
        self.db_user = db_user or settings.postgres_user
        self.db_password = db_password or settings.postgres_password
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;hasura_client&#x22;" type="&#x22;HasuraClient | None&#x22;" value="&#x22;None&#x22;">
      HasuraClient instance for API operations.
    </PyParameter>

    <PyParameter name="&#x22;db_host&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      PostgreSQL host (default: from HasuraPostgresSettings).
    </PyParameter>

    <PyParameter name="&#x22;db_port&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;">
      PostgreSQL port (default: from HasuraPostgresSettings).
    </PyParameter>

    <PyParameter name="&#x22;db_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      PostgreSQL database name (default: from HasuraPostgresSettings).
    </PyParameter>

    <PyParameter name="&#x22;db_user&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      PostgreSQL username (default: from HasuraPostgresSettings).
    </PyParameter>

    <PyParameter name="&#x22;db_password&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      PostgreSQL password (default: from HasuraPostgresSettings).
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;_get_db_connection&#x22;" type="&#x22;(self)&#x22;">
  Get PostgreSQL database connection.

  Creates and returns a psycopg2 connection with autocommit enabled.
  The connection is configured with the resolved host and port.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > conn = tracker.\_get\_db\_connection()
    > > > cursor = conn.cursor()
    > > > cursor.execute("SELECT version()")
  </Callout>

  <PySourceCode>
    ```python
    def _get_db_connection(self):
        """Get PostgreSQL database connection.

        Creates and returns a psycopg2 connection with autocommit enabled.
        The connection is configured with the resolved host and port.

        Returns:
            psycopg2 connection object with ISOLATION_LEVEL_AUTOCOMMIT.

        Raises:
            psycopg2.Error: If connection fails.

        Example:
            >>> conn = tracker._get_db_connection()
            >>> cursor = conn.cursor()
            >>> cursor.execute("SELECT version()")

        """
        conn = psycopg2.connect(
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="null">
    psycopg2 connection object with ISOLATION\_LEVEL\_AUTOCOMMIT.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;discover_user_schemas&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  Discover all user schemas that contain tables.

  Queries the database to find all schemas that:

  * Have at least one base table
  * Are not system schemas (pg\_\*, information\_schema, etc.)

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > schemas = tracker.discover\_user\_schemas()
    > > > print(schemas)
    > > > \['api', 'marts', 'public']
  </Callout>

  <PySourceCode>
    ```python
    def discover_user_schemas(self) -> list[str]:
        """Discover all user schemas that contain tables.

        Queries the database to find all schemas that:
        - Have at least one base table
        - Are not system schemas (pg_*, information_schema, etc.)

        Returns:
            Sorted list of schema names containing user tables.

        Raises:
            psycopg2.Error: If database query fails.

        Example:
            >>> schemas = tracker.discover_user_schemas()
            >>> print(schemas)
            ['api', 'marts', 'public']

        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT DISTINCT table_schema
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE'
                  AND table_schema NOT LIKE 'pg_%%'
                  AND table_schema != 'information_schema'
                ORDER BY table_schema
                """
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    Sorted list of schema names containing user tables.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_tables_in_schema&#x22;" type="&#x22;(self, schema) -> list[str]&#x22;">
  Get all tables in a schema.

  Queries the information\_schema to find all base tables
  within the specified database schema.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > tables = tracker.get\_tables\_in\_schema("api")
    > > > print(tables)
    > > > \['customers', 'orders', 'products']
  </Callout>

  <PySourceCode>
    ```python
    def get_tables_in_schema(self, schema: str) -> list[str]:
        """Get all tables in a schema.

        Queries the information_schema to find all base tables
        within the specified database schema.

        Args:
            schema: Schema name to query.

        Returns:
            Sorted list of table names in the schema.

        Raises:
            psycopg2.Error: If database query fails.

        Example:
            >>> tables = tracker.get_tables_in_schema("api")
            >>> print(tables)
            ['customers', 'orders', 'products']

        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """,
                (schema,),
            )

            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name to query.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    Sorted list of table names in the schema.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_foreign_keys&#x22;" type="&#x22;(self, schema, table) -> list[dict]&#x22;">
  Get foreign key constraints for a table.

  Queries the information\_schema to find all foreign key
  relationships defined on the specified table.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > fks = tracker.get\_foreign\_keys("api", "orders")
    > > > for fk in fks:
    > > > ...     print(f"\{fk\['local\_column']} -> \{fk\['ref\_table']}.\{fk\['ref\_column']}")
    > > > customer\_id -> customers.id
  </Callout>

  <PySourceCode>
    ```python
    def get_foreign_keys(self, schema: str, table: str) -> list[dict]:
        """Get foreign key constraints for a table.

        Queries the information_schema to find all foreign key
        relationships defined on the specified table.

        Args:
            schema: Schema name containing the table.
            table: Table name to query for foreign keys.

        Returns:
            List of foreign key dictionaries with keys:
                - local_column: Column in the source table
                - ref_schema: Schema of referenced table
                - ref_table: Name of referenced table
                - ref_column: Column in referenced table

        Raises:
            psycopg2.Error: If database query fails.

        Example:
            >>> fks = tracker.get_foreign_keys("api", "orders")
            >>> for fk in fks:
            ...     print(f"{fk['local_column']} -> {fk['ref_table']}.{fk['ref_column']}")
            customer_id -> customers.id

        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    kcu.column_name,
                    ccu.table_schema,
                    ccu.table_name,
                    ccu.column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = %s
                    AND tc.table_name = %s
                ORDER BY kcu.column_name
            """,
                (schema, table),
            )

            fks = []
            for local_col, ref_schema, ref_table, ref_col in cursor.fetchall():
                fks.append(
                    {
                        "local_column": local_col,
                        "ref_schema": ref_schema,
                        "ref_table": ref_table,
                        "ref_column": ref_col,
                    }
                )

            return fks
        finally:
            cursor.close()
            conn.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name containing the table.
    </PyParameter>

    <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name to query for foreign keys.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of foreign key dictionaries with keys:

    * local\_column: Column in the source table
    * ref\_schema: Schema of referenced table
    * ref\_table: Name of referenced table
    * ref\_column: Column in referenced table
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;track_tables&#x22;" type="&#x22;(self, schema, exclude=None, verbose=True) -> dict[str, bool]&#x22;">
  Track all tables in a schema.

  Discovers all tables in the specified schema and tracks them
  in Hasura, optionally excluding specific tables.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > results = tracker.track\_tables("api")
    > > > print(f"Tracked \{sum(results.values())}/\{len(results)} tables")
    > > > results = tracker.track\_tables("api", exclude=\["temp\_table"])
  </Callout>

  <PySourceCode>
    ```python
    def track_tables(
        self, schema: str, exclude: list[str] | None = None, verbose: bool = True
    ) -> dict[str, bool]:
        """Track all tables in a schema.

        Discovers all tables in the specified schema and tracks them
        in Hasura, optionally excluding specific tables.

        Args:
            schema: Schema name to track tables from.
            exclude: List of table names to skip (default: None).
            verbose: Print progress messages (default: True).

        Returns:
            Dictionary mapping table_name -> success boolean.

        Raises:
            requests.RequestException: If Hasura API calls fail.
            psycopg2.Error: If database queries fail.

        Example:
            >>> results = tracker.track_tables("api")
            >>> print(f"Tracked {sum(results.values())}/{len(results)} tables")
            >>> results = tracker.track_tables("api", exclude=["temp_table"])

        """
        if verbose:
            logger.info("Discovering tables in schema '%s'...", schema)

        tables = self.get_tables_in_schema(schema)
        exclude = exclude or []
        tables = [t for t in tables if t not in exclude]

        if verbose:
            logger.info("Found %s tables", len(tables))

        results = {}
        for table in tables:
            try:
                if verbose:
                    logger.info("Tracking %s.%s...", schema, table)

                self.client.track_table(schema, table)
                results[table] = True

                if verbose:
                    logger.info("Tracking %s.%s ✓", schema, table)
            except Exception as e:
                results[table] = False
                if verbose:
                    logger.warning("Tracking %s.%s ✗ (%s)", schema, table, str(e)[:200])

        return results
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name to track tables from.
    </PyParameter>

    <PyParameter name="&#x22;exclude&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      List of table names to skip (default: None).
    </PyParameter>

    <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      Print progress messages (default: True).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary mapping table\_name -> success boolean.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;setup_relationships&#x22;" type="&#x22;(self, schema, verbose=True) -> dict[tuple[str, str], bool]&#x22;">
  Auto-create relationships from foreign keys.

  Discovers foreign key constraints in all tables of the schema
  and creates corresponding object relationships in Hasura.

  Relationship names are derived from the local column name by
  removing '\_id' suffix (e.g., 'customer\_id' -> 'customer').

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > results = tracker.setup\_relationships("api")
    > > > for (table, rel), success in results.items():
    > > > ...     status = "created" if success else "failed"
    > > > ...     print(f"\{table}.\{rel}: \{status}")
  </Callout>

  <PySourceCode>
    ```python
    def setup_relationships(self, schema: str, verbose: bool = True) -> dict[tuple[str, str], bool]:
        """Auto-create relationships from foreign keys.

        Discovers foreign key constraints in all tables of the schema
        and creates corresponding object relationships in Hasura.

        Relationship names are derived from the local column name by
        removing '_id' suffix (e.g., 'customer_id' -> 'customer').

        Args:
            schema: Schema name to set up relationships in.
            verbose: Print progress messages (default: True).

        Returns:
            Dictionary mapping (table, relationship_name) -> success boolean.

        Raises:
            requests.RequestException: If Hasura API calls fail.
            psycopg2.Error: If database queries fail.

        Example:
            >>> results = tracker.setup_relationships("api")
            >>> for (table, rel), success in results.items():
            ...     status = "created" if success else "failed"
            ...     print(f"{table}.{rel}: {status}")

        """
        tables = self.get_tables_in_schema(schema)
        results = {}

        for table in tables:
            fks = self.get_foreign_keys(schema, table)

            for fk in fks:
                rel_name = fk["local_column"].replace("_id", "")

                try:
                    if verbose:
                        logger.info(
                            "Creating relationship %s.%s -> %s...",
                            table,
                            rel_name,
                            fk["ref_table"],
                        )

                    self.client.create_object_relationship(
                        schema,
                        table,
                        rel_name,
                        manual_configuration={
                            "foreign_key_constraint_on": fk["local_column"],
                        },
                    )

                    results[(table, rel_name)] = True
                    if verbose:
                        logger.info("Creating relationship %s.%s ✓", table, rel_name)
                except Exception as e:
                    results[(table, rel_name)] = False
                    if verbose:
                        logger.warning(
                            "Creating relationship %s.%s ✗ (%s)", table, rel_name, str(e)[:200]
                        )

        return results
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name to set up relationships in.
    </PyParameter>

    <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      Print progress messages (default: True).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary mapping (table, relationship\_name) -> success boolean.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;setup_default_permissions&#x22;" type="&#x22;(self, schema, verbose=True) -> dict[tuple[str, str], bool]&#x22;">
  Set up default permissions for tables.

  Creates default SELECT permissions for standard roles (anon, analyst, admin)
  on all tables in the specified schema. The 'anon' role gets full access,
  while 'analyst' and 'admin' get standard access.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > results = tracker.setup\_default\_permissions("api")
    > > > print(f"Created \{sum(results.values())} permissions")
  </Callout>

  <PySourceCode>
    ```python
    def setup_default_permissions(
        self, schema: str, verbose: bool = True
    ) -> dict[tuple[str, str], bool]:
        """Set up default permissions for tables.

        Creates default SELECT permissions for standard roles (anon, analyst, admin)
        on all tables in the specified schema. The 'anon' role gets full access,
        while 'analyst' and 'admin' get standard access.

        Args:
            schema: Schema name to set up permissions in.
            verbose: Print progress messages (default: True).

        Returns:
            Dictionary mapping (table, role) -> success boolean.

        Raises:
            requests.RequestException: If Hasura API calls fail.
            psycopg2.Error: If database queries fail.

        Example:
            >>> results = tracker.setup_default_permissions("api")
            >>> print(f"Created {sum(results.values())} permissions")

        """
        tables = self.get_tables_in_schema(schema)
        results = {}

        # Default: allow anon users to view api schema
        default_permissions = [
            ("anon", {"allow_aggregations": True}),
            ("analyst", {}),
            ("admin", {}),
        ]

        for table in tables:
            for role, filter_expr in default_permissions:
                try:
                    if verbose:
                        logger.info("Creating permission %s.%s...", table, role)

                    self.client.create_select_permission(schema, table, role, filter=filter_expr)

                    results[(table, role)] = True
                    if verbose:
                        logger.info("Creating permission %s.%s ✓", table, role)
                except Exception as e:
                    results[(table, role)] = False
                    if verbose:
                        logger.warning(
                            "Creating permission %s.%s ✗ (%s)", table, role, str(e)[:200]
                        )

        return results
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name to set up permissions in.
    </PyParameter>

    <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      Print progress messages (default: True).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary mapping (table, role) -> success boolean.
  </PyFunctionReturn>
</PyFunction>
