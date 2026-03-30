# TrinoResource (/docs/python-reference/packages/phlo-trino/phlo_trino/resource/TrinoResource)



Resource wrapper for Trino connections and query execution.

Attributes [#attributes]

<PyAttribute name="&#x22;host&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Optional Trino host override.
</PyAttribute>

<PyAttribute name="&#x22;port&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;">
  Optional Trino port override.
</PyAttribute>

<PyAttribute name="&#x22;user&#x22;" type="&#x22;str&#x22;" value="&#x22;'dagster'&#x22;">
  Trino username for connections.
</PyAttribute>

<PyAttribute name="&#x22;catalog&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Optional catalog override.
</PyAttribute>

<PyAttribute name="&#x22;ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Optional Nessie ref override for catalog resolution.
</PyAttribute>

<PyAttribute name="&#x22;runtime&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="&#x22;None&#x22;">
  Optional runtime context providing canonical ref routing.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;_resolved_ref&#x22;" type="&#x22;(self) -> str | None&#x22;">
  Resolve the effective ref for Trino catalog routing.

  <PySourceCode>
    ```python
    def _resolved_ref(self) -> str | None:
        """Resolve the effective ref for Trino catalog routing.

        Returns:
            Resolved reference string or None if using default.

        """
        return resolve_runtime_ref(
            self.runtime,
            support=TRINO_QUERY_ENGINE_SUPPORT,
            default_ref=self.ref or config.default_catalog_ref,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;">
    Resolved reference string or None if using default.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_resolved_catalog&#x22;" type="&#x22;(self) -> str&#x22;">
  Resolve the catalog name, including non-main Nessie refs.

  <PySourceCode>
    ```python
    def _resolved_catalog(self) -> str:
        """Resolve the catalog name, including non-main Nessie refs.

        Returns:
            Catalog name used for Trino connections.

        """
        base_catalog = self.catalog or config.trino_catalog
        ref = self._resolved_ref()
        if ref and ref != "main":
            return f"{base_catalog}_{ref}"
        return base_catalog
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Catalog name used for Trino connections.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_connection&#x22;" type="&#x22;(self, schema=None)&#x22;">
  Create a DB-API connection to Trino.

  <PySourceCode>
    ```python
    def get_connection(self, schema: str | None = None):
        """Create a DB-API connection to Trino.

        Args:
            schema: Optional schema name for the connection.

        Returns:
            Open Trino DB-API connection.

        """
        return connect(
            host=self.host or config.trino_host,
            port=self.port or config.trino_port,
            user=self.user,
            catalog=self._resolved_catalog(),
            schema=schema,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional schema name for the connection.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null">
    Open Trino DB-API connection.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;cursor&#x22;" type="&#x22;(self, schema=None)&#x22;">
  Yield a Trino cursor and close resources on exit.

  <PySourceCode>
    ```python
    @contextmanager
    def cursor(self, schema: str | None = None):
        """Yield a Trino cursor and close resources on exit.

        Args:
            schema: Optional schema name for the connection.

        Yields:
            Active Trino cursor.

        """
        conn = self.get_connection(schema=schema)
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            try:
                cursor.close()
            finally:
                conn.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional schema name for the connection.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, sql, params=None, schema=None)&#x22;">
  Execute SQL and return query results when present.

  <PySourceCode>
    ```python
    def execute(self, sql: str, params: Iterable[object] | None = None, schema: str | None = None):
        """Execute SQL and return query results when present.

        Args:
            sql: SQL statement to execute.
            params: Optional positional query parameters.
            schema: Optional schema name for the connection.

        Returns:
            List of query result rows, or an empty list for statements without results.

        """
        params = list(params or [])
        with self.cursor(schema=schema) as cursor:
            cursor.execute(sql, params)
            if cursor.description is None:
                return []
            return cursor.fetchall()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;sql&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL statement to execute.
    </PyParameter>

    <PyParameter name="&#x22;params&#x22;" type="&#x22;Iterable[object] | None&#x22;" value="&#x22;None&#x22;">
      Optional positional query parameters.
    </PyParameter>

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional schema name for the connection.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null">
    List of query result rows, or an empty list for statements without results.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;wait_ready&#x22;" type="&#x22;(self, *, timeout=60.0, interval=1.0, schema=None) -> None&#x22;">
  Wait for Trino to accept queries, retrying on startup/connection errors.

  Polls Trino with "SELECT 1" until successful or timeout exceeded.
  Automatically retries on transient connection errors.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > trino = TrinoResource()
    > > > trino.wait\_ready(timeout=30.0, interval=2.0)
  </Callout>

  <PySourceCode>
    ```python
    def wait_ready(
        self,
        *,
        timeout: float = 60.0,
        interval: float = 1.0,
        schema: str | None = None,
    ) -> None:
        """Wait for Trino to accept queries, retrying on startup/connection errors.

        Polls Trino with "SELECT 1" until successful or timeout exceeded.
        Automatically retries on transient connection errors.

        Args:
            timeout: Maximum seconds to wait before raising TimeoutError.
            interval: Seconds between retry attempts.
            schema: Optional schema name for the test query.

        Raises:
            TimeoutError: If Trino is not ready within the timeout period.
            Exception: If a non-transient error occurs.

        Example:
            >>> trino = TrinoResource()
            >>> trino.wait_ready(timeout=30.0, interval=2.0)

        """
        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        interval = max(interval, 0.0)
        while time.monotonic() < deadline:
            try:
                self.execute("SELECT 1", schema=schema)
                logger.info(
                    "trino_wait_ready_succeeded",
                    host=self.host or config.trino_host,
                    port=self.port or config.trino_port,
                    schema=schema,
                )
                return
            except Exception as exc:  # noqa: BLE001 - surface real error after timeout
                if not _is_transient_trino_error(exc):
                    logger.exception(
                        "trino_wait_ready_non_transient_error",
                        host=self.host or config.trino_host,
                        port=self.port or config.trino_port,
                        schema=schema,
                    )
                    raise
                last_error = exc
                logger.debug(
                    "trino_wait_ready_retry",
                    host=self.host or config.trino_host,
                    port=self.port or config.trino_port,
                    schema=schema,
                    retry_interval_seconds=interval,
                )
                time.sleep(interval)
        logger.error(
            "trino_wait_ready_timeout",
            host=self.host or config.trino_host,
            port=self.port or config.trino_port,
            schema=schema,
            timeout_seconds=timeout,
        )
        raise TimeoutError(f"Trino not ready after {timeout:.1f}s") from last_error
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;float&#x22;" value="&#x22;60.0&#x22;">
      Maximum seconds to wait before raising TimeoutError.
    </PyParameter>

    <PyParameter name="&#x22;interval&#x22;" type="&#x22;float&#x22;" value="&#x22;1.0&#x22;">
      Seconds between retry attempts.
    </PyParameter>

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional schema name for the test query.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, host=None, port=None, user='dagster', catalog=None, ref=None, runtime=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;host&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;port&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;user&#x22;" type="&#x22;str&#x22;" value="&#x22;'dagster'&#x22;" />

    <PyParameter name="&#x22;catalog&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;runtime&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
