# PostgresResource (/docs/python-reference/packages/phlo-postgres/phlo_postgres/resource/PostgresResource)



Lightweight PostgreSQL connection resource with connection pooling.

This class manages PostgreSQL connections using a connection pool for efficiency.
It supports both context manager usage (recommended) and manual lifecycle management.
Transactions are automatically handled when using the transactional\_cursor context manager.

Attributes [#attributes]

<PyAttribute name="&#x22;host&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  PostgreSQL server hostname. Uses settings default if None.
</PyAttribute>

<PyAttribute name="&#x22;port&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;">
  PostgreSQL server port. Uses settings default if None.
</PyAttribute>

<PyAttribute name="&#x22;user&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Database username. Uses settings default if None.
</PyAttribute>

<PyAttribute name="&#x22;password&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Database password. Uses settings default if None.
</PyAttribute>

<PyAttribute name="&#x22;database&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Database name. Uses settings default if None.
</PyAttribute>

<PyAttribute name="&#x22;min_connections&#x22;" type="&#x22;int&#x22;" value="&#x22;1&#x22;">
  Minimum number of connections to maintain in the pool.
</PyAttribute>

<PyAttribute name="&#x22;max_connections&#x22;" type="&#x22;int&#x22;" value="&#x22;5&#x22;">
  Maximum number of connections allowed in the pool.
</PyAttribute>

<PyAttribute name="&#x22;_pool&#x22;" type="&#x22;pool.SimpleConnectionPool | None&#x22;" value="&#x22;field(default=None, init=False, repr=False)&#x22;">
  Internal connection pool instance (initialized on first use).
</PyAttribute>

<PyAttribute name="&#x22;_connection&#x22;" type="&#x22;Any | None&#x22;" value="&#x22;field(default=None, init=False, repr=False)&#x22;">
  Active connection from the pool (acquired on demand).
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__enter__&#x22;" type="&#x22;(self) -> 'PostgresResource'&#x22;">
  Initialize the resource for context-managed usage.

  This method ensures a connection is available when entering the context.
  The connection is automatically returned to the pool when exiting.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > with PostgresResource() as db:
    > > > ...     # Connection is now active
    > > > ...     db.execute("SELECT 1")
  </Callout>

  <PySourceCode>
    ```python
    def __enter__(self) -> "PostgresResource":
        """Initialize the resource for context-managed usage.

        This method ensures a connection is available when entering the context.
        The connection is automatically returned to the pool when exiting.

        Returns:
            PostgresResource: The initialized resource instance ready for queries.

        Example:
            >>> with PostgresResource() as db:
            ...     # Connection is now active
            ...     db.execute("SELECT 1")

        """
        self._ensure_connection()
        return self
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;'PostgresResource'&#x22;">
    The initialized resource instance ready for queries.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__exit__&#x22;" type="&#x22;(self, exc_type, exc, tb) -> None&#x22;">
  Clean up the resource on context exit.

  Performs rollback if an exception occurred, then returns the connection
  to the pool and closes the pool.

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    Rollback is attempted on exception but failures are logged, not raised,
    to ensure the original exception propagates.
  </Callout>

  <PySourceCode>
    ```python
    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """Clean up the resource on context exit.

        Performs rollback if an exception occurred, then returns the connection
        to the pool and closes the pool.

        Args:
            exc_type: Exception type raised in the context, if any.
            exc: Exception instance raised in the context, if any.
            tb: Traceback object for the raised exception, if any.

        Note:
            Rollback is attempted on exception but failures are logged, not raised,
            to ensure the original exception propagates.

        """
        if exc_type is not None:
            try:
                self.rollback()
            except Exception:  # noqa: BLE001 - best effort rollback on context exit
                logger.warning("postgres_resource_rollback_failed", exc_info=True)
        try:
            self.close()
        finally:
            self.close_pool()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;exc_type&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Exception type raised in the context, if any.
    </PyParameter>

    <PyParameter name="&#x22;exc&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Exception instance raised in the context, if any.
    </PyParameter>

    <PyParameter name="&#x22;tb&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Traceback object for the raised exception, if any.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__del__&#x22;" type="&#x22;(self) -> None&#x22;">
  Best-effort cleanup during object destruction.

  Attempts to close the connection and pool if the object is garbage collected
  without proper cleanup. Failures are silently logged to prevent destruction
  errors from interfering with program termination.

  <PySourceCode>
    ```python
    def __del__(self) -> None:
        """Best-effort cleanup during object destruction.

        Attempts to close the connection and pool if the object is garbage collected
        without proper cleanup. Failures are silently logged to prevent destruction
        errors from interfering with program termination.
        """
        try:
            self.close()
        except Exception:  # noqa: BLE001 - destructor must never raise
            logger.debug("postgres_resource_close_on_del_failed", exc_info=True)
        try:
            self.close_pool()
        except Exception:  # noqa: BLE001 - destructor must never raise
            logger.debug("postgres_resource_pool_close_on_del_failed", exc_info=True)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_ensure_pool&#x22;" type="&#x22;(self) -> pool.SimpleConnectionPool&#x22;">
  Create or return the connection pool.

  Lazy-initializes the connection pool on first access using configured or
  default settings. Connection parameters are resolved in order:
  explicit attribute > settings default > built-in default.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > db = PostgresResource()
    > > > pool = db.\_ensure\_pool()  # Creates pool on first call
    > > > same\_pool = db.\_ensure\_pool()  # Returns existing pool
  </Callout>

  <PySourceCode>
    ```python
    def _ensure_pool(self) -> pool.SimpleConnectionPool:
        """Create or return the connection pool.

        Lazy-initializes the connection pool on first access using configured or
        default settings. Connection parameters are resolved in order:
        explicit attribute > settings default > built-in default.

        Returns:
            pool.SimpleConnectionPool: The active connection pool.

        Raises:
            psycopg2.Error: If pool creation fails (e.g., bad credentials, host unreachable).

        Example:
            >>> db = PostgresResource()
            >>> pool = db._ensure_pool()  # Creates pool on first call
            >>> same_pool = db._ensure_pool()  # Returns existing pool

        """
        if self._pool is None or self._pool.closed:
            settings = get_settings()
            host = self.host or settings.postgres_host
            port = self.port or settings.postgres_port
            database = self.database or settings.postgres_db
            start = perf_counter()
            logger.info(
                "postgres_pool_creation_started",
                host=host,
                port=port,
                database=database,
                min_connections=self.min_connections,
                max_connections=self.max_connections,
            )
            try:
                self._pool = pool.SimpleConnectionPool(
                    minconn=self.min_connections,
                    maxconn=self.max_connections,
                    host=host,
                    port=port,
                    user=self.user or settings.postgres_user,
                    password=self.password or settings.postgres_password,
                    dbname=database,
                )
            except Exception:
                logger.error(
                    "postgres_pool_creation_failed",
                    host=host,
                    port=port,
                    database=database,
                    elapsed_ms=round((perf_counter() - start) * 1000, 2),
                    exc_info=True,
                )
                raise
            logger.info(
                "postgres_pool_creation_completed",
                host=host,
                port=port,
                database=database,
                elapsed_ms=round((perf_counter() - start) * 1000, 2),
            )
        return self._pool
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;psycopg2.pool.SimpleConnectionPool&#x22;">
    pool.SimpleConnectionPool: The active connection pool.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_ensure_connection&#x22;" type="&#x22;(self)&#x22;">
  Acquire a connection from the pool.

  Returns a healthy connection from the pool, creating the pool if needed.
  Stale connections are detected and replaced automatically.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > db = PostgresResource()
    > > > conn = db.\_ensure\_connection()
    > > > with conn.cursor() as cur:
    > > > ...     cur.execute("SELECT 1")
  </Callout>

  <PySourceCode>
    ```python
    def _ensure_connection(self):
        """Acquire a connection from the pool.

        Returns a healthy connection from the pool, creating the pool if needed.
        Stale connections are detected and replaced automatically.

        Returns:
            Any: Active psycopg2 connection object.

        Raises:
            psycopg2.Error: If connection acquisition fails.

        Example:
            >>> db = PostgresResource()
            >>> conn = db._ensure_connection()
            >>> with conn.cursor() as cur:
            ...     cur.execute("SELECT 1")

        """
        if self._connection is None or getattr(self._connection, "closed", 1):
            connection_pool = self._ensure_pool()
            # Return the stale connection slot before acquiring a new one
            if self._connection is not None:
                try:
                    connection_pool.putconn(self._connection, close=True)
                except Exception:  # noqa: BLE001 - best effort return
                    logger.debug("postgres_resource_stale_connection_return_failed", exc_info=True)
                self._connection = None
            start = perf_counter()
            logger.info("postgres_resource_connection_started")
            try:
                self._connection = connection_pool.getconn()
            except Exception:
                logger.error(
                    "postgres_resource_connection_failed",
                    elapsed_ms=round((perf_counter() - start) * 1000, 2),
                    exc_info=True,
                )
                raise
            logger.info(
                "postgres_resource_connection_completed",
                elapsed_ms=round((perf_counter() - start) * 1000, 2),
            )
        return self._connection
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="null">
    Active psycopg2 connection object.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;cursor&#x22;" type="&#x22;(self)&#x22;">
  Provide a cursor for manual transaction control.

  Yields a psycopg2 cursor. The caller is responsible for committing or
  rolling back transactions. Useful when you need fine-grained control
  over transaction boundaries.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > with PostgresResource() as db:
    > > > ...     with db.cursor() as cur:
    > > > ...         cur.execute("BEGIN")
    > > > ...         cur.execute("INSERT INTO logs VALUES (%s)", ("entry",))
    > > > ...         # Manual commit/rollback based on business logic
    > > > ...         cur.execute("COMMIT")
  </Callout>

  <PySourceCode>
    ```python
    @contextmanager
    def cursor(self):
        """Provide a cursor for manual transaction control.

        Yields a psycopg2 cursor. The caller is responsible for committing or
        rolling back transactions. Useful when you need fine-grained control
        over transaction boundaries.

        Yields:
            psycopg2.cursor: Database cursor ready for query execution.

        Example:
            >>> with PostgresResource() as db:
            ...     with db.cursor() as cur:
            ...         cur.execute("BEGIN")
            ...         cur.execute("INSERT INTO logs VALUES (%s)", ("entry",))
            ...         # Manual commit/rollback based on business logic
            ...         cur.execute("COMMIT")

        """
        connection = self._ensure_connection()
        cursor = connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;transactional_cursor&#x22;" type="&#x22;(self)&#x22;">
  Provide a cursor with automatic commit/rollback handling.

  Yields a cursor and automatically commits on success or rolls back on
  exception. This is the recommended way to perform write operations.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > with PostgresResource() as db:
    > > > ...     try:
    > > > ...         with db.transactional\_cursor() as cur:
    > > > ...             cur.execute("INSERT INTO events (msg) VALUES (%s)", ("click",))
    > > > ...             cur.execute("UPDATE counters SET count = count + 1")
    > > > ...             # Both operations committed atomically on success
    > > > ...     except psycopg2.Error:
    > > > ...         # Both operations rolled back on failure
    > > > ...         pass
  </Callout>

  <PySourceCode>
    ```python
    @contextmanager
    def transactional_cursor(self):
        """Provide a cursor with automatic commit/rollback handling.

        Yields a cursor and automatically commits on success or rolls back on
        exception. This is the recommended way to perform write operations.

        Yields:
            psycopg2.cursor: Database cursor ready for query execution.

        Raises:
            Exception: Re-raises any exception after performing rollback.

        Example:
            >>> with PostgresResource() as db:
            ...     try:
            ...         with db.transactional_cursor() as cur:
            ...             cur.execute("INSERT INTO events (msg) VALUES (%s)", ("click",))
            ...             cur.execute("UPDATE counters SET count = count + 1")
            ...             # Both operations committed atomically on success
            ...     except psycopg2.Error:
            ...         # Both operations rolled back on failure
            ...         pass

        """
        connection = self._ensure_connection()
        cursor = connection.cursor()
        start = perf_counter()
        logger.info("postgres_transaction_started")
        try:
            yield cursor
        except Exception:
            logger.warning(
                "postgres_transaction_rollback",
                elapsed_ms=round((perf_counter() - start) * 1000, 2),
                exc_info=True,
            )
            connection.rollback()
            raise
        else:
            connection.commit()
            logger.info(
                "postgres_transaction_committed",
                elapsed_ms=round((perf_counter() - start) * 1000, 2),
            )
        finally:
            cursor.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;commit&#x22;" type="&#x22;(self) -> None&#x22;">
  Commit the current transaction explicitly.

  Commits any pending changes in the current connection. Use this when
  managing transactions manually with the cursor() context manager.

  Example:

  > > > with PostgresResource() as db:
  > > > ...     with db.cursor() as cur:
  > > > ...         cur.execute("INSERT INTO logs VALUES (%s)", ("entry",))
  > > > ...     db.commit()  # Explicit commit

  <PySourceCode>
    ```python
    def commit(self) -> None:
        """Commit the current transaction explicitly.

        Commits any pending changes in the current connection. Use this when
        managing transactions manually with the cursor() context manager.

        Example:
            >>> with PostgresResource() as db:
            ...     with db.cursor() as cur:
            ...         cur.execute("INSERT INTO logs VALUES (%s)", ("entry",))
            ...     db.commit()  # Explicit commit

        """
        start = perf_counter()
        self._ensure_connection().commit()
        logger.info(
            "postgres_commit_completed",
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;rollback&#x22;" type="&#x22;(self) -> None&#x22;">
  Roll back the current transaction explicitly.

  Reverts any pending changes in the current connection. Use this when
  managing transactions manually and an error occurs.

  Example:

  > > > with PostgresResource() as db:
  > > > ...     with db.cursor() as cur:
  > > > ...         try:
  > > > ...             cur.execute("INSERT INTO logs VALUES (%s)", ("entry",))
  > > > ...         except psycopg2.Error:
  > > > ...             db.rollback()
  > > > ...             raise

  <PySourceCode>
    ```python
    def rollback(self) -> None:
        """Roll back the current transaction explicitly.

        Reverts any pending changes in the current connection. Use this when
        managing transactions manually and an error occurs.

        Example:
            >>> with PostgresResource() as db:
            ...     with db.cursor() as cur:
            ...         try:
            ...             cur.execute("INSERT INTO logs VALUES (%s)", ("entry",))
            ...         except psycopg2.Error:
            ...             db.rollback()
            ...             raise

        """
        start = perf_counter()
        self._ensure_connection().rollback()
        logger.info(
            "postgres_rollback_completed",
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;close&#x22;" type="&#x22;(self) -> None&#x22;">
  Return the current connection to the pool.

  Returns the active connection to the pool for reuse by other operations.
  Safe to call multiple times; subsequent calls are no-ops.

  Example:

  > > > db = PostgresResource()
  > > > db.\_ensure\_connection()
  > > >
  > > > ... do work ... [#-do-work-]
  > > >
  > > > db.close()  # Return connection to pool

  <PySourceCode>
    ```python
    def close(self) -> None:
        """Return the current connection to the pool.

        Returns the active connection to the pool for reuse by other operations.
        Safe to call multiple times; subsequent calls are no-ops.

        Example:
            >>> db = PostgresResource()
            >>> db._ensure_connection()
            >>> # ... do work ...
            >>> db.close()  # Return connection to pool

        """
        if self._connection is not None and self._pool is not None:
            start = perf_counter()
            logger.info("postgres_resource_connection_return_started")
            try:
                self._pool.putconn(self._connection)
            except Exception:
                logger.warning("postgres_resource_connection_return_failed", exc_info=True)
                raise
            logger.info(
                "postgres_resource_connection_return_completed",
                elapsed_ms=round((perf_counter() - start) * 1000, 2),
            )
        self._connection = None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;close_pool&#x22;" type="&#x22;(self) -> None&#x22;">
  Close all connections in the pool.

  Closes all connections in the pool and releases associated resources.
  Safe to call multiple times; subsequent calls are no-ops.

  Warning:
  This terminates all pooled connections. Ensure no operations are
  in progress before calling.

  Example:

  > > > db = PostgresResource()
  > > >
  > > > ... do work ... [#-do-work--1]
  > > >
  > > > db.close\_pool()  # Clean shutdown

  <PySourceCode>
    ```python
    def close_pool(self) -> None:
        """Close all connections in the pool.

        Closes all connections in the pool and releases associated resources.
        Safe to call multiple times; subsequent calls are no-ops.

        Warning:
            This terminates all pooled connections. Ensure no operations are
            in progress before calling.

        Example:
            >>> db = PostgresResource()
            >>> # ... do work ...
            >>> db.close_pool()  # Clean shutdown

        """
        if self._pool is not None and not self._pool.closed:
            start = perf_counter()
            logger.info("postgres_pool_close_started")
            try:
                self._pool.closeall()
            except Exception:
                logger.warning("postgres_pool_close_failed", exc_info=True)
                raise
            logger.info(
                "postgres_pool_close_completed",
                elapsed_ms=round((perf_counter() - start) * 1000, 2),
            )
        self._pool = None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;is_healthy&#x22;" type="&#x22;(self) -> bool&#x22;">
  Check if the database connection is alive and responsive.

  Performs a simple health check by executing "SELECT 1" and returns
  True if the query succeeds.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > with PostgresResource() as db:
    > > > ...     if db.is\_healthy():
    > > > ...         print("Database is up")
    > > > ...     else:
    > > > ...         print("Database connection failed")
  </Callout>

  <PySourceCode>
    ```python
    def is_healthy(self) -> bool:
        """Check if the database connection is alive and responsive.

        Performs a simple health check by executing "SELECT 1" and returns
        True if the query succeeds.

        Returns:
            bool: True if the connection is healthy, False otherwise.

        Example:
            >>> with PostgresResource() as db:
            ...     if db.is_healthy():
            ...         print("Database is up")
            ...     else:
            ...         print("Database connection failed")

        """
        try:
            conn = self._ensure_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception:
            logger.warning("postgres_health_check_failed", exc_info=True)
            return False
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if the connection is healthy, False otherwise.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, sql_stmt, params=None) -> None&#x22;">
  Execute a SQL statement without returning results.

  Executes a SQL statement (INSERT, UPDATE, DELETE, DDL, etc.) and
  commits the transaction immediately. For queries that return data,
  use query() or query\_one() instead.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > with PostgresResource() as db:
    > > > ...     # DDL
    > > > ...     db.execute("CREATE TABLE users (id SERIAL PRIMARY KEY)")
    > > > ...     # DML with parameters
    > > > ...     db.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))
  </Callout>

  <PySourceCode>
    ```python
    def execute(self, sql_stmt: str, params: tuple | None = None) -> None:
        """Execute a SQL statement without returning results.

        Executes a SQL statement (INSERT, UPDATE, DELETE, DDL, etc.) and
        commits the transaction immediately. For queries that return data,
        use query() or query_one() instead.

        Args:
            sql_stmt: SQL statement to execute. Can include placeholders (%s).
            params: Tuple of parameters to substitute into the SQL statement.

        Raises:
            psycopg2.Error: If the SQL execution fails.

        Example:
            >>> with PostgresResource() as db:
            ...     # DDL
            ...     db.execute("CREATE TABLE users (id SERIAL PRIMARY KEY)")
            ...     # DML with parameters
            ...     db.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))

        """
        start = perf_counter()
        logger.info("postgres_execute_started")
        with self.cursor() as cur:
            cur.execute(sql_stmt, params)
        self.commit()
        logger.info(
            "postgres_execute_completed",
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;sql_stmt&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL statement to execute. Can include placeholders (%s).
    </PyParameter>

    <PyParameter name="&#x22;params&#x22;" type="&#x22;tuple | None&#x22;" value="&#x22;None&#x22;">
      Tuple of parameters to substitute into the SQL statement.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;query&#x22;" type="&#x22;(self, sql_stmt, params=None) -> list[tuple]&#x22;">
  Execute a SQL query and return all result rows.

  Executes a SELECT query and returns all rows as a list of tuples.
  For large result sets, consider using a cursor directly to stream results.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > with PostgresResource() as db:
    > > > ...     # Simple query
    > > > ...     rows = db.query("SELECT id, name FROM users")
    > > > ...     # Parameterized query
    > > > ...     rows = db.query("SELECT \* FROM users WHERE age > %s", (18,))
    > > > ...     for user\_id, name in rows:
    > > > ...         print(f"\{user\_id}: \{name}")
  </Callout>

  <PySourceCode>
    ```python
    def query(self, sql_stmt: str, params: tuple | None = None) -> list[tuple]:
        """Execute a SQL query and return all result rows.

        Executes a SELECT query and returns all rows as a list of tuples.
        For large result sets, consider using a cursor directly to stream results.

        Args:
            sql_stmt: SQL SELECT statement. Can include placeholders (%s).
            params: Tuple of parameters to substitute into the SQL statement.

        Returns:
            list[tuple]: All rows returned by the query. Empty list if no results.

        Raises:
            psycopg2.Error: If the query execution fails.

        Example:
            >>> with PostgresResource() as db:
            ...     # Simple query
            ...     rows = db.query("SELECT id, name FROM users")
            ...     # Parameterized query
            ...     rows = db.query("SELECT * FROM users WHERE age > %s", (18,))
            ...     for user_id, name in rows:
            ...         print(f"{user_id}: {name}")

        """
        start = perf_counter()
        logger.info("postgres_query_started")
        with self.cursor() as cur:
            cur.execute(sql_stmt, params)
            rows = cur.fetchall()
        logger.info(
            "postgres_query_completed",
            row_count=len(rows),
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
        )
        return rows
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;sql_stmt&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL SELECT statement. Can include placeholders (%s).
    </PyParameter>

    <PyParameter name="&#x22;params&#x22;" type="&#x22;tuple | None&#x22;" value="&#x22;None&#x22;">
      Tuple of parameters to substitute into the SQL statement.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[tuple]: All rows returned by the query. Empty list if no results.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;query_one&#x22;" type="&#x22;(self, sql_stmt, params=None) -> tuple | None&#x22;">
  Execute a SQL query and return the first result row.

  Executes a SELECT query and returns only the first row, or None if
  no results. Useful for queries expected to return at most one row
  (e.g., lookups by primary key).

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > with PostgresResource() as db:
    > > > ...     # Lookup by ID
    > > > ...     row = db.query\_one("SELECT \* FROM users WHERE id = %s", (42,))
    > > > ...     if row:
    > > > ...         user\_id, name, email = row
    > > > ...     # Aggregate query
    > > > ...     count\_row = db.query\_one("SELECT COUNT(\*) FROM users")
    > > > ...     user\_count = count\_row\[0] if count\_row else 0
  </Callout>

  <PySourceCode>
    ```python
    def query_one(self, sql_stmt: str, params: tuple | None = None) -> tuple | None:
        """Execute a SQL query and return the first result row.

        Executes a SELECT query and returns only the first row, or None if
        no results. Useful for queries expected to return at most one row
        (e.g., lookups by primary key).

        Args:
            sql_stmt: SQL SELECT statement. Can include placeholders (%s).
            params: Tuple of parameters to substitute into the SQL statement.

        Returns:
            tuple | None: First row as a tuple, or None if query returns no rows.

        Raises:
            psycopg2.Error: If the query execution fails.

        Example:
            >>> with PostgresResource() as db:
            ...     # Lookup by ID
            ...     row = db.query_one("SELECT * FROM users WHERE id = %s", (42,))
            ...     if row:
            ...         user_id, name, email = row
            ...     # Aggregate query
            ...     count_row = db.query_one("SELECT COUNT(*) FROM users")
            ...     user_count = count_row[0] if count_row else 0

        """
        start = perf_counter()
        logger.info("postgres_query_one_started")
        with self.cursor() as cur:
            cur.execute(sql_stmt, params)
            row = cur.fetchone()
        logger.info(
            "postgres_query_one_completed",
            has_result=row is not None,
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
        )
        return row
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;sql_stmt&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL SELECT statement. Can include placeholders (%s).
    </PyParameter>

    <PyParameter name="&#x22;params&#x22;" type="&#x22;tuple | None&#x22;" value="&#x22;None&#x22;">
      Tuple of parameters to substitute into the SQL statement.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;tuple | None&#x22;">
    tuple | None: First row as a tuple, or None if query returns no rows.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;ensure_schema&#x22;" type="&#x22;(self, schema_name) -> None&#x22;">
  Create a database schema if it does not exist.

  Idempotent schema creation using CREATE SCHEMA IF NOT EXISTS.
  Safe to call multiple times; subsequent calls are no-ops if the
  schema already exists.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > with PostgresResource() as db:
    > > > ...     # Create analytics schema
    > > > ...     db.ensure\_schema("analytics")
    > > > ...     # Create table in the new schema
    > > > ...     db.execute("CREATE TABLE analytics.events (id SERIAL)")
  </Callout>

  <PySourceCode>
    ```python
    def ensure_schema(self, schema_name: str) -> None:
        """Create a database schema if it does not exist.

        Idempotent schema creation using CREATE SCHEMA IF NOT EXISTS.
        Safe to call multiple times; subsequent calls are no-ops if the
        schema already exists.

        Args:
            schema_name: Name of the schema to create.

        Raises:
            psycopg2.Error: If schema creation fails (e.g., permission denied).

        Example:
            >>> with PostgresResource() as db:
            ...     # Create analytics schema
            ...     db.ensure_schema("analytics")
            ...     # Create table in the new schema
            ...     db.execute("CREATE TABLE analytics.events (id SERIAL)")

        """
        with self.transactional_cursor() as cur:
            cur.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema_name))
            )
        logger.info("postgres_schema_ensured", schema_name=schema_name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of the schema to create.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, host=None, port=None, user=None, password=None, database=None, min_connections=1, max_connections=5) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;host&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;port&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;user&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;password&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;database&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;min_connections&#x22;" type="&#x22;int&#x22;" value="&#x22;1&#x22;" />

    <PyParameter name="&#x22;max_connections&#x22;" type="&#x22;int&#x22;" value="&#x22;5&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
