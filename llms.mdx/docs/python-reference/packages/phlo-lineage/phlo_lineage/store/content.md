# store (/docs/python-reference/packages/phlo-lineage/phlo_lineage/store)



Row-level and column-level lineage store for Phlo.

This module provides PostgreSQL-backed persistence for tracking data lineage
at both the row and column levels. It uses ULIDs (Universally Unique
Lexicographically Sortable Identifiers) for row identification and supports
deterministic querying of provenance information.

The LineageStore class is the primary interface, providing:

* Row-level lineage tracking with parent-child relationships
* Column-level lineage mappings between assets
* Asset node and edge management for graph construction
* Batch operations for efficient bulk inserts
* Recursive queries for ancestor/descendant traversal

Example:

> > > from phlo\_lineage.store import LineageStore, generate\_row\_id
> > > store = LineageStore("postgresql://user:pass\@localhost:5432/phlo")
> > > row\_id = generate\_row\_id()
> > > store.record\_row(row\_id, "bronze.orders", "dlt")

Architecture:

* Schema auto-creation on first use via SQL migration files
* Class-level schema initialization flag for performance
* Connection pooling via psycopg2 context managers
* JSONB columns for flexible metadata storage

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;ColumnLineage&#x22;" href="&#x22;/docs/python-reference/packages/phlo-lineage/phlo_lineage/store/ColumnLineage&#x22;" />

      <Card title="&#x22;LineageStore&#x22;" href="&#x22;/docs/python-reference/packages/phlo-lineage/phlo_lineage/store/LineageStore&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;resolve_lineage_db_url&#x22;" type="&#x22;() -> str | None&#x22;">
      Resolve the lineage database URL from explicit lineage environment variables.

      Checks a prioritized list of environment variables for the PostgreSQL
      connection string used by the lineage store.

      <Callout title="&#x22;Priority order&#x22;" type="&#x22;priority-order&#x22;">
        1. LINEAGE\_DB\_URL
        2. PHLO\_LINEAGE\_DB\_URL
        3. DAGSTER\_PG\_DB\_CONNECTION\_STRING
      </Callout>

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > import os
        > > > os.environ\["LINEAGE\_DB\_URL"] = "postgresql://localhost/lineage"
        > > > resolve\_lineage\_db\_url()
        > > > 'postgresql://localhost/lineage'
      </Callout>

      <PySourceCode>
        ```python
        def resolve_lineage_db_url() -> str | None:
            """Resolve the lineage database URL from explicit lineage environment variables.

            Checks a prioritized list of environment variables for the PostgreSQL
            connection string used by the lineage store.

            Priority order:
                1. LINEAGE_DB_URL
                2. PHLO_LINEAGE_DB_URL
                3. DAGSTER_PG_DB_CONNECTION_STRING

            Returns:
                PostgreSQL connection string if found, otherwise None.

            Example:
                >>> import os
                >>> os.environ["LINEAGE_DB_URL"] = "postgresql://localhost/lineage"
                >>> resolve_lineage_db_url()
                'postgresql://localhost/lineage'

            """
            for key in _LINEAGE_DB_KEYS:
                value = os.environ.get(key)
                if value:
                    return value
            return None
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        PostgreSQL connection string if found, otherwise None.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;resolve_lineage_db_url_with_postgres_fallback&#x22;" type="&#x22;() -> str | None&#x22;">
      Resolve the lineage database URL with PostgreSQL fallback.

      First attempts to resolve from explicit lineage environment variables.
      If not found, constructs a connection string from standard PostgreSQL
      environment variables with sensible defaults.

      <Callout title="&#x22;Environment variables used for fallback&#x22;" type="&#x22;environment-variables-used-for-fallback&#x22;">
        * POSTGRES\_HOST (default: "postgres")
        * POSTGRES\_PORT (default: 5432)
        * POSTGRES\_USER (default: "phlo")
        * POSTGRES\_PASSWORD (default: "phlo")
        * POSTGRES\_DB (default: "phlo")
      </Callout>

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > import os
        > > > os.environ\["POSTGRES\_HOST"] = "localhost"
        > > > url = resolve\_lineage\_db\_url\_with\_postgres\_fallback()
        > > > assert "localhost" in url
      </Callout>

      <PySourceCode>
        ```python
        def resolve_lineage_db_url_with_postgres_fallback() -> str | None:
            """Resolve the lineage database URL with PostgreSQL fallback.

            First attempts to resolve from explicit lineage environment variables.
            If not found, constructs a connection string from standard PostgreSQL
            environment variables with sensible defaults.

            Environment variables used for fallback:
                - POSTGRES_HOST (default: "postgres")
                - POSTGRES_PORT (default: 5432)
                - POSTGRES_USER (default: "phlo")
                - POSTGRES_PASSWORD (default: "phlo")
                - POSTGRES_DB (default: "phlo")

            Returns:
                PostgreSQL connection string or None if resolution fails.

            Example:
                >>> import os
                >>> os.environ["POSTGRES_HOST"] = "localhost"
                >>> url = resolve_lineage_db_url_with_postgres_fallback()
                >>> assert "localhost" in url

            """
            if connection_string := resolve_lineage_db_url():
                return connection_string
            host, port = _resolve_postgres_host(
                os.environ.get("POSTGRES_HOST", "postgres"),
                int(os.environ.get("POSTGRES_PORT", "5432")),
            )
            user = quote_plus(os.environ.get("POSTGRES_USER", "phlo"))
            password = quote_plus(os.environ.get("POSTGRES_PASSWORD", "phlo"))
            database = quote_plus(os.environ.get("POSTGRES_DB", "phlo"))
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        PostgreSQL connection string or None if resolution fails.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_resolve_postgres_host&#x22;" type="&#x22;(host, port) -> tuple[str, int]&#x22;">
      Resolve PostgreSQL host and port with network configuration.

      Uses the phlo network configuration system to resolve hostnames and
      handle Docker network scenarios.

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        This is an internal helper function used by resolve\_lineage\_db\_url\_with\_postgres\_fallback.
      </Callout>

      <PySourceCode>
        ```python
        def _resolve_postgres_host(host: str, port: int) -> tuple[str, int]:
            """Resolve PostgreSQL host and port with network configuration.

            Uses the phlo network configuration system to resolve hostnames and
            handle Docker network scenarios.

            Args:
                host: Hostname or IP address of the PostgreSQL server.
                port: Port number for the PostgreSQL connection.

            Returns:
                Tuple of (resolved_host, resolved_port).

            Note:
                This is an internal helper function used by resolve_lineage_db_url_with_postgres_fallback.

            """
            return resolve_host(host, port, port_env_var="POSTGRES_PORT")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;host&#x22;" type="&#x22;str&#x22;" value="undefined">
          Hostname or IP address of the PostgreSQL server.
        </PyParameter>

        <PyParameter name="&#x22;port&#x22;" type="&#x22;int&#x22;" value="undefined">
          Port number for the PostgreSQL connection.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;tuple&#x22;">
        Tuple of (resolved\_host, resolved\_port).
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;generate_row_id&#x22;" type="&#x22;() -> str&#x22;">
      Generate a new ULID for row-level lineage tracking.

      ULIDs (Universally Unique Lexicographically Sortable Identifiers) provide:

      * Lexicographic sortability by timestamp (48-bit timestamp prefix)
      * Global uniqueness (128-bit total entropy)
      * URL safety (Crockford's Base32 encoding)
      * Monotonic sort order within the same millisecond

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > row\_id = generate\_row\_id()
        > > > len(row\_id)  # ULIDs are 26 characters
        > > > 26
        > > > import time
        > > >
        > > > ULIDs sort by time [#ulids-sort-by-time]
        > > >
        > > > id1 = generate\_row\_id()
        > > > time.sleep(0.01)
        > > > id2 = generate\_row\_id()
        > > > id1 \< id2
        > > > True
      </Callout>

      <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
        [https://github.com/ulid/spec](https://github.com/ulid/spec) for ULID specification details.
      </Callout>

      <PySourceCode>
        ```python
        def generate_row_id() -> str:
            """Generate a new ULID for row-level lineage tracking.

            ULIDs (Universally Unique Lexicographically Sortable Identifiers) provide:
                - Lexicographic sortability by timestamp (48-bit timestamp prefix)
                - Global uniqueness (128-bit total entropy)
                - URL safety (Crockford's Base32 encoding)
                - Monotonic sort order within the same millisecond

            Returns:
                String representation of a new ULID.

            Example:
                >>> row_id = generate_row_id()
                >>> len(row_id)  # ULIDs are 26 characters
                26
                >>> import time
                >>> # ULIDs sort by time
                >>> id1 = generate_row_id()
                >>> time.sleep(0.01)
                >>> id2 = generate_row_id()
                >>> id1 < id2
                True

            See Also:
                https://github.com/ulid/spec for ULID specification details.

            """
            return str(ulid.ULID())
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str&#x22;">
        String representation of a new ULID.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
