# track (/docs/python-reference/packages/phlo-hasura/phlo_hasura/track)



Hasura table tracking and auto-discovery.

This module provides classes and functions for automatically discovering
and tracking PostgreSQL tables in Hasura. It handles schema discovery,
foreign key relationship detection, and bulk table operations.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;HasuraPostgresSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-hasura/phlo_hasura/track/HasuraPostgresSettings&#x22;" />

      <Card title="&#x22;HasuraTableTracker&#x22;" href="&#x22;/docs/python-reference/packages/phlo-hasura/phlo_hasura/track/HasuraTableTracker&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_resolve_db_host&#x22;" type="&#x22;(host, port) -> tuple[str, int]&#x22;">
      Resolve database host, falling back to localhost if Docker hostname unreachable.

      When running hooks from the host machine, Docker internal hostnames like 'postgres'
      won't resolve. In that case, use localhost with the exposed port.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > host, port = \_resolve\_db\_host("postgres", 5432)
        > > >
        > > > If running outside Docker: [#if-running-outside-docker]
        > > >
        > > > host = "localhost", port = 5432 (or from POSTGRES_PORT env) [#host--localhost-port--5432-or-from-postgres_port-env]
      </Callout>

      <PySourceCode>
        ```python
        def _resolve_db_host(host: str, port: int) -> tuple[str, int]:
            """Resolve database host, falling back to localhost if Docker hostname unreachable.

            When running hooks from the host machine, Docker internal hostnames like 'postgres'
            won't resolve. In that case, use localhost with the exposed port.

            Args:
                host: Database host (may be Docker internal hostname like 'postgres').
                port: Database port (may be internal port).

            Returns:
                Tuple of (resolved_host, resolved_port) suitable for connection.
                If Docker hostname fails to resolve, returns ('localhost', POSTGRES_PORT).

            Example:
                >>> host, port = _resolve_db_host("postgres", 5432)
                >>> # If running outside Docker:
                >>> # host = "localhost", port = 5432 (or from POSTGRES_PORT env)

            """
            # If already localhost, use as-is
            if host in ("localhost", "127.0.0.1"):
                return host, port

            # Try to resolve the hostname
            try:
                socket.gethostbyname(host)
                return host, port
            except socket.gaierror:
                # Can't resolve - we're likely running on the host, not in Docker
                # Use localhost with the exposed port from environment
                exposed_port = int(os.environ.get("POSTGRES_PORT", port))
                logger.debug(
                    "Cannot resolve '%s', using localhost:%s (running outside Docker)",
                    host,
                    exposed_port,
                )
                return "localhost", exposed_port
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;host&#x22;" type="&#x22;str&#x22;" value="undefined">
          Database host (may be Docker internal hostname like 'postgres').
        </PyParameter>

        <PyParameter name="&#x22;port&#x22;" type="&#x22;int&#x22;" value="undefined">
          Database port (may be internal port).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Tuple of (resolved\_host, resolved\_port) suitable for connection.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;auto_track&#x22;" type="&#x22;(schema='api', verbose=True) -> dict[str, Any]&#x22;">
      Convenience function to auto-track all tables in a schema.

      Performs complete auto-configuration of a schema: tracks all tables,
      creates relationships from foreign keys, and sets up default permissions.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > results = auto\_track("api")
        > > > print(f"Tables: \{sum(results\['tables'].values())}/\{len(results\['tables'])}")
      </Callout>

      <PySourceCode>
        ```python
        def auto_track(schema: str = "api", verbose: bool = True) -> dict[str, Any]:
            """Convenience function to auto-track all tables in a schema.

            Performs complete auto-configuration of a schema: tracks all tables,
            creates relationships from foreign keys, and sets up default permissions.

            Args:
                schema: Schema name to auto-configure (default: "api").
                verbose: Print progress messages (default: True).

            Returns:
                Dictionary containing tracking results:
                {
                    "tables": {table_name: success_bool, ...},
                    "relationships": {(table, rel): success_bool, ...},
                    "permissions": {(table, role): success_bool, ...}
                }

            Raises:
                requests.RequestException: If Hasura API calls fail.
                psycopg2.Error: If database queries fail.

            Example:
                >>> results = auto_track("api")
                >>> print(f"Tables: {sum(results['tables'].values())}/{len(results['tables'])}")

            """
            if verbose:
                logger.info("=" * 60)
                logger.info("Hasura Auto-Track")
                logger.info("=" * 60)

            tracker = HasuraTableTracker()

            # Track tables
            track_results = tracker.track_tables(schema, verbose=verbose)
            if verbose:
                logger.info("")

            # Setup relationships
            if verbose:
                logger.info("Setting up relationships...")
            rel_results = tracker.setup_relationships(schema, verbose=verbose)
            if verbose:
                logger.info("")

            # Setup default permissions
            if verbose:
                logger.info("Setting up default permissions...")
            perm_results = tracker.setup_default_permissions(schema, verbose=verbose)

            if verbose:
                logger.info("=" * 60)
                logger.info("✓ Auto-track completed")
                logger.info(
                    "  Tables tracked: %s/%s",
                    sum(1 for v in track_results.values() if v),
                    len(track_results),
                )
                logger.info(
                    "  Relationships: %s/%s",
                    sum(1 for v in rel_results.values() if v),
                    len(rel_results),
                )
                logger.info(
                    "  Permissions: %s/%s",
                    sum(1 for v in perm_results.values() if v),
                    len(perm_results),
                )
                logger.info("=" * 60)

            return {
                "tables": track_results,
                "relationships": rel_results,
                "permissions": perm_results,
            }
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="&#x22;'api'&#x22;">
          Schema name to auto-configure (default: "api").
        </PyParameter>

        <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Print progress messages (default: True).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary containing tracking results:
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;auto_track_all&#x22;" type="&#x22;(verbose=True) -> dict[str, dict[str, Any]]&#x22;">
      Auto-discover and track all tables in all user schemas.

      Discovers all non-system schemas containing tables and runs
      auto\_track() on each one.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > all\_results = auto\_track\_all()
        > > > for schema, results in all\_results.items():
        > > > ...     tracked = sum(results\['tables'].values())
        > > > ...     print(f"\{schema}: \{tracked} tables tracked")
      </Callout>

      <PySourceCode>
        ```python
        def auto_track_all(verbose: bool = True) -> dict[str, dict[str, Any]]:
            """Auto-discover and track all tables in all user schemas.

            Discovers all non-system schemas containing tables and runs
            auto_track() on each one.

            Args:
                verbose: Print progress messages (default: True).

            Returns:
                Dictionary mapping schema_name -> tracking results dict.
                Each schema's results contains tables, relationships, and permissions.

            Raises:
                requests.RequestException: If Hasura API calls fail.
                psycopg2.Error: If database queries fail.

            Example:
                >>> all_results = auto_track_all()
                >>> for schema, results in all_results.items():
                ...     tracked = sum(results['tables'].values())
                ...     print(f"{schema}: {tracked} tables tracked")

            """
            if verbose:
                logger.info("=" * 60)
                logger.info("Hasura Auto-Track (All Schemas)")
                logger.info("=" * 60)

            tracker = HasuraTableTracker()
            schemas = tracker.discover_user_schemas()

            if verbose:
                logger.info("Discovered %d user schemas: %s", len(schemas), ", ".join(schemas))
                logger.info("")

            results: dict[str, dict[str, Any]] = {}
            for schema in schemas:
                if verbose:
                    logger.info("Processing schema: %s", schema)
                results[schema] = auto_track(schema=schema, verbose=verbose)

            if verbose:
                logger.info("=" * 60)
                logger.info("✓ All schemas processed")
                total_tables = sum(len(r.get("tables", {})) for r in results.values())
                tracked_tables = sum(
                    sum(1 for v in r.get("tables", {}).values() if v) for r in results.values()
                )
                logger.info("  Total tables tracked: %d/%d", tracked_tables, total_tables)
                logger.info("=" * 60)

            return results
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Print progress messages (default: True).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary mapping schema\_name -> tracking results dict.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
