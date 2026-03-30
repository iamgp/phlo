# LineageStore (/docs/python-reference/packages/phlo-lineage/phlo_lineage/store/LineageStore)



PostgreSQL-backed store for row-level and column-level lineage.

This class provides comprehensive CRUD operations for tracking data provenance
across the pipeline. The schema is auto-created on first use, requiring
zero manual configuration.

Attributes [#attributes]

<PyAttribute name="&#x22;connection_string&#x22;" type="null" value="&#x22;connection_string&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, connection_string)&#x22;">
  Initialize a LineageStore instance.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > store = LineageStore("postgresql://user:pass\@localhost:5432/dagster")
  </Callout>

  <PySourceCode>
    ```python
    def __init__(self, connection_string: str):
        """Initialize a LineageStore instance.

        Args:
            connection_string: PostgreSQL connection string. Must include all
                necessary authentication and host information.

        Example:
            >>> store = LineageStore("postgresql://user:pass@localhost:5432/dagster")

        """
        self.connection_string = connection_string
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;connection_string&#x22;" type="&#x22;str&#x22;" value="undefined">
      PostgreSQL connection string. Must include all
      necessary authentication and host information.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;_ensure_schema&#x22;" type="&#x22;(self) -> None&#x22;">
  Ensure the lineage schema exists, creating it if necessary.

  This method is called automatically before any database operation.
  It uses a class-level flag to ensure schema initialization only happens
  once per process, even with multiple LineageStore instances.

  <Callout title="&#x22;The initialization process&#x22;" type="&#x22;the-initialization-process&#x22;">
    1. Check if the class-level flag indicates schema is ready
    2. Verify schema existence via to\_regclass queries
    3. If missing, execute all SQL migration files in order
    4. Handle race conditions gracefully (duplicate creation attempts)
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    This is an internal method called automatically by public methods.
    Manual invocation is not required.
  </Callout>

  <PySourceCode>
    ```python
    def _ensure_schema(self) -> None:
        """Ensure the lineage schema exists, creating it if necessary.

        This method is called automatically before any database operation.
        It uses a class-level flag to ensure schema initialization only happens
        once per process, even with multiple LineageStore instances.

        The initialization process:
            1. Check if the class-level flag indicates schema is ready
            2. Verify schema existence via to_regclass queries
            3. If missing, execute all SQL migration files in order
            4. Handle race conditions gracefully (duplicate creation attempts)

        Raises:
            Exception: If schema creation fails for reasons other than
                already-exists conditions. Warnings are logged for errors.

        Note:
            This is an internal method called automatically by public methods.
            Manual invocation is not required.

        """
        if LineageStore._schema_initialized:
            return

        if self._schema_exists():
            LineageStore._schema_initialized = True
            return

        try:
            self.setup_schema()
            LineageStore._schema_initialized = True
        except Exception as e:
            if self._schema_exists() or "already exists" in str(e).lower():
                LineageStore._schema_initialized = True
            else:
                logger.warning("lineage_schema_init_failed", error=str(e))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_schema_exists&#x22;" type="&#x22;(self) -> bool&#x22;">
  Check if the lineage schema tables exist.

  Verifies existence of the three core lineage tables using PostgreSQL's
  to\_regclass function, which returns the OID if the relation exists.

  <Callout title="&#x22;Tables checked&#x22;" type="&#x22;tables-checked&#x22;">
    * phlo.asset\_lineage\_nodes
    * phlo.asset\_lineage\_edges
    * phlo.column\_lineage
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    This is an internal helper method. Connection errors are caught
    and result in a False return value rather than propagating.
  </Callout>

  <PySourceCode>
    ```python
    def _schema_exists(self) -> bool:
        """Check if the lineage schema tables exist.

        Verifies existence of the three core lineage tables using PostgreSQL's
        to_regclass function, which returns the OID if the relation exists.

        Tables checked:
            - phlo.asset_lineage_nodes
            - phlo.asset_lineage_edges
            - phlo.column_lineage

        Returns:
            True if all three core tables exist, False otherwise.

        Note:
            This is an internal helper method. Connection errors are caught
            and result in a False return value rather than propagating.

        """
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            to_regclass('phlo.asset_lineage_nodes'),
                            to_regclass('phlo.asset_lineage_edges'),
                            to_regclass('phlo.column_lineage')
                        """
                    )
                    result = cur.fetchone()
        except Exception:
            return False
        if result is None:
            return False
        return all(value is not None for value in result)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if all three core tables exist, False otherwise.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;setup_schema&#x22;" type="&#x22;(self) -> None&#x22;">
  Create the lineage schema and tables by executing SQL migrations.

  Reads all .sql files from the package's sql/ directory and executes them
  in sorted order. This supports incremental schema migrations through
  numbered migration files (e.g., 001\_initial.sql, 002\_add\_indexes.sql).

  <Callout title="&#x22;Migration files are located relative to this module at&#x22;" type="&#x22;migration-files-are-located-relative-to-this-module-at&#x22;">
    \{package\_root}/sql/\*.sql
  </Callout>

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > store = LineageStore("postgresql://...")
    > > > store.setup\_schema()  # Creates tables if they don't exist
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    This method is typically called automatically by \_ensure\_schema().
    Manual invocation is useful for explicit schema management or
    when integrating with external migration systems.
  </Callout>

  <PySourceCode>
    ```python
    def setup_schema(self) -> None:
        """Create the lineage schema and tables by executing SQL migrations.

        Reads all .sql files from the package's sql/ directory and executes them
        in sorted order. This supports incremental schema migrations through
        numbered migration files (e.g., 001_initial.sql, 002_add_indexes.sql).

        Migration files are located relative to this module at:
            {package_root}/sql/*.sql

        Raises:
            Exception: If SQL execution fails for any migration file.

        Example:
            >>> store = LineageStore("postgresql://...")
            >>> store.setup_schema()  # Creates tables if they don't exist

        Note:
            This method is typically called automatically by _ensure_schema().
            Manual invocation is useful for explicit schema management or
            when integrating with external migration systems.

        """
        sql_dir = Path(__file__).parent / "sql"
        sql_files = sorted(sql_dir.glob("*.sql"))

        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                for sql_file in sql_files:
                    cur.execute(sql_file.read_text())
            conn.commit()

        logger.info("lineage_schema_setup_complete", migration_count=len(sql_files))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;record_row&#x22;" type="&#x22;(self, row_id, table_name, source_type='dlt', parent_row_ids=None, metadata=None) -> None&#x22;">
  Record lineage information for a single row.

  Inserts or updates a row lineage record with full provenance information.
  Uses UPSERT semantics (INSERT ... ON CONFLICT) to handle duplicate row IDs
  by updating the existing record with new values.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > store.record\_row(
    > > > ...     row\_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
    > > > ...     table\_name="bronze.orders",
    > > > ...     source\_type="dlt",
    > > > ...     parent\_row\_ids=\[],
    > > > ...     metadata=\{"run\_id": "run-123", "source": "api"},
    > > > ... )
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    This operation is logged at INFO level on success and WARNING
    level on failure. Parent row count is included in log context.
  </Callout>

  <PySourceCode>
    ```python
    def record_row(
        self,
        row_id: str,
        table_name: str,
        source_type: str = "dlt",
        parent_row_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record lineage information for a single row.

        Inserts or updates a row lineage record with full provenance information.
        Uses UPSERT semantics (INSERT ... ON CONFLICT) to handle duplicate row IDs
        by updating the existing record with new values.

        Args:
            row_id: ULID identifier for the row, typically generated via
                generate_row_id(). Must be unique across all tables.
            table_name: Fully qualified table name in "schema.table" format
                (e.g., "bronze.dlt_events", "silver.stg_orders").
            source_type: Origin classification for the row. Common values:
                - "dlt": Data loaded via dlt (data load tool)
                - "dbt": Data transformed via dbt
                - "external": Data from external systems
                - "manual": User-inserted data
            parent_row_ids: List of ULIDs for parent rows that this row was
                derived from. Empty or None for root-level (source) rows.
            metadata: Optional dictionary with additional context such as
                run_id, partition keys, or custom attributes. Stored as JSONB.

        Raises:
            Exception: Re-raised after logging if database operation fails.

        Example:
            >>> store.record_row(
            ...     row_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
            ...     table_name="bronze.orders",
            ...     source_type="dlt",
            ...     parent_row_ids=[],
            ...     metadata={"run_id": "run-123", "source": "api"},
            ... )

        Note:
            This operation is logged at INFO level on success and WARNING
            level on failure. Parent row count is included in log context.

        """
        parent_count = len(parent_row_ids or [])
        logger.info(
            "lineage_record_row_started",
            table_name=table_name,
            source_type=source_type,
            parent_row_count=parent_count,
        )
        try:
            self._ensure_schema()
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO phlo.row_lineage
                        (row_id, table_name, source_type, parent_row_ids, metadata)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (row_id) DO UPDATE SET
                            table_name = EXCLUDED.table_name,
                            source_type = EXCLUDED.source_type,
                            parent_row_ids = EXCLUDED.parent_row_ids,
                            metadata = EXCLUDED.metadata
                        """,
                        (
                            row_id,
                            table_name,
                            source_type,
                            parent_row_ids,
                            json.dumps(metadata) if metadata else None,
                        ),
                    )
                conn.commit()
            logger.info(
                "lineage_record_row_succeeded",
                table_name=table_name,
                source_type=source_type,
                parent_row_count=parent_count,
            )
        except Exception:
            logger.warning(
                "lineage_record_row_failed",
                table_name=table_name,
                source_type=source_type,
                parent_row_count=parent_count,
                exc_info=True,
            )
            raise
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;row_id&#x22;" type="&#x22;str&#x22;" value="undefined">
      ULID identifier for the row, typically generated via
      generate\_row\_id(). Must be unique across all tables.
    </PyParameter>

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name in "schema.table" format
      (e.g., "bronze.dlt\_events", "silver.stg\_orders").
    </PyParameter>

    <PyParameter name="&#x22;source_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'dlt'&#x22;">
      Origin classification for the row. Common values:

      * "dlt": Data loaded via dlt (data load tool)
      * "dbt": Data transformed via dbt
      * "external": Data from external systems
      * "manual": User-inserted data
    </PyParameter>

    <PyParameter name="&#x22;parent_row_ids&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      List of ULIDs for parent rows that this row was
      derived from. Empty or None for root-level (source) rows.
    </PyParameter>

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Optional dictionary with additional context such as
      run\_id, partition keys, or custom attributes. Stored as JSONB.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;record_rows_batch&#x22;" type="&#x22;(self, rows, table_name, source_type='dlt', metadata=None) -> int&#x22;">
  Record lineage for multiple rows in a single batch operation.

  Efficiently inserts lineage records for many rows using execute\_values
  for bulk loading. Rows without "\_phlo\_row\_id" field are silently skipped.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > rows = \[
    > > > ...     \{"\_phlo\_row\_id": "01ARZ...", "order\_id": 1},
    > > > ...     \{"\_phlo\_row\_id": "01ARZ...", "order\_id": 2},
    > > > ... ]
    > > > count = store.record\_rows\_batch(rows, "bronze.orders", "dlt")
    > > > print(f"Recorded \{count} rows")
  </Callout>

  <Callout title="&#x22;Performance&#x22;" type="&#x22;performance&#x22;">
    Uses psycopg2.extras.execute\_values for O(1) round trips regardless
    of batch size (up to PostgreSQL parameter limits).
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    Duplicate row\_ids are silently ignored (ON CONFLICT DO NOTHING).
    To update existing records, use record\_row() individually.
  </Callout>

  <PySourceCode>
    ```python
    def record_rows_batch(
        self,
        rows: list[dict[str, Any]],
        table_name: str,
        source_type: str = "dlt",
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Record lineage for multiple rows in a single batch operation.

        Efficiently inserts lineage records for many rows using execute_values
        for bulk loading. Rows without "_phlo_row_id" field are silently skipped.

        Args:
            rows: List of row dictionaries, each must contain "_phlo_row_id" key
                with a valid ULID value.
            table_name: Fully qualified destination table name.
            source_type: Origin classification (see record_row() for options).
            metadata: Metadata dictionary applied to all rows in the batch.

        Returns:
            Number of rows successfully recorded (may be less than input length
            if some rows lack _phlo_row_id).

        Raises:
            Exception: Re-raised after logging if batch insert fails.

        Example:
            >>> rows = [
            ...     {"_phlo_row_id": "01ARZ...", "order_id": 1},
            ...     {"_phlo_row_id": "01ARZ...", "order_id": 2},
            ... ]
            >>> count = store.record_rows_batch(rows, "bronze.orders", "dlt")
            >>> print(f"Recorded {count} rows")

        Performance:
            Uses psycopg2.extras.execute_values for O(1) round trips regardless
            of batch size (up to PostgreSQL parameter limits).

        Note:
            Duplicate row_ids are silently ignored (ON CONFLICT DO NOTHING).
            To update existing records, use record_row() individually.

        """
        if not rows:
            return 0

        requested_count = len(rows)
        values = []
        for row in rows:
            row_id = row.get("_phlo_row_id")
            if not row_id:
                continue
            values.append(
                (
                    row_id,
                    table_name,
                    source_type,
                    None,  # parent_row_ids
                    json.dumps(metadata) if metadata else None,
                )
            )

        if not values:
            return 0

        inserted_count = len(values)
        skipped_count = requested_count - inserted_count
        logger.info(
            "lineage_record_rows_batch_started",
            table_name=table_name,
            source_type=source_type,
            requested_count=requested_count,
            insert_count=inserted_count,
            skipped_missing_row_id_count=skipped_count,
        )
        try:
            self._ensure_schema()
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Use execute_values for efficient batch insert
                    from psycopg2.extras import execute_values

                    execute_values(
                        cur,
                        """
                        INSERT INTO phlo.row_lineage
                        (row_id, table_name, source_type, parent_row_ids, metadata)
                        VALUES %s
                        ON CONFLICT (row_id) DO NOTHING
                        """,
                        values,
                    )
                conn.commit()
            logger.info(
                "lineage_record_rows_batch_succeeded",
                table_name=table_name,
                source_type=source_type,
                requested_count=requested_count,
                insert_count=inserted_count,
                skipped_missing_row_id_count=skipped_count,
            )
        except Exception:
            logger.warning(
                "lineage_record_rows_batch_failed",
                table_name=table_name,
                source_type=source_type,
                requested_count=requested_count,
                insert_count=inserted_count,
                skipped_missing_row_id_count=skipped_count,
                exc_info=True,
            )
            raise

        return len(values)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;rows&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="undefined">
      List of row dictionaries, each must contain "\_phlo\_row\_id" key
      with a valid ULID value.
    </PyParameter>

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified destination table name.
    </PyParameter>

    <PyParameter name="&#x22;source_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'dlt'&#x22;">
      Origin classification (see record\_row() for options).
    </PyParameter>

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Metadata dictionary applied to all rows in the batch.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;">
    Number of rows successfully recorded (may be less than input length
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;record_asset_nodes&#x22;" type="&#x22;(self, asset_keys, *, asset_type=None, status=None, description=None, metadata=None, tags=None) -> int&#x22;">
  Record or update asset nodes in the lineage graph.

  Creates or updates asset metadata records. Duplicate keys trigger
  UPSERT semantics with COALESCE for optional fields (existing non-null
  values are preserved if new values are None).

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > store.record\_asset\_nodes(
    > > > ...     \["bronze.orders", "silver.stg\_orders"],
    > > > ...     asset\_type="ingestion",
    > > > ...     status="success",
    > > > ...     metadata=\{"owner": "data-team"},
    > > > ... )
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    The updated\_at timestamp is automatically refreshed on every UPSERT.
    COALESCE logic preserves existing non-null values when upserting
    partial updates.
  </Callout>

  <PySourceCode>
    ```python
    def record_asset_nodes(
        self,
        asset_keys: list[str],
        *,
        asset_type: str | None = None,
        status: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: dict[str, Any] | None = None,
    ) -> int:
        """Record or update asset nodes in the lineage graph.

        Creates or updates asset metadata records. Duplicate keys trigger
        UPSERT semantics with COALESCE for optional fields (existing non-null
        values are preserved if new values are None).

        Args:
            asset_keys: List of unique asset identifiers (e.g., "bronze.orders",
                "silver.stg_orders").
            asset_type: Classification of the asset. Common values:
                - "ingestion": Raw loaded data
                - "transform": dbt model or transformation output
                - "publish": Final published dataset
            status: Current status of the asset:
                - "success": Successfully materialized
                - "warning": Completed with warnings
                - "failure": Failed or stale
                - "unknown": Status not determined
            description: Human-readable description of the asset.
            metadata: JSON-serializable dictionary with arbitrary asset metadata.
            tags: Dictionary of string tags for categorization and filtering.

        Returns:
            Number of asset nodes successfully persisted.

        Raises:
            Exception: Re-raised after logging if database operation fails.

        Example:
            >>> store.record_asset_nodes(
            ...     ["bronze.orders", "silver.stg_orders"],
            ...     asset_type="ingestion",
            ...     status="success",
            ...     metadata={"owner": "data-team"},
            ... )

        Note:
            The updated_at timestamp is automatically refreshed on every UPSERT.
            COALESCE logic preserves existing non-null values when upserting
            partial updates.

        """
        if not asset_keys:
            return 0

        unique_keys = sorted(set(asset_keys))
        values = [
            (
                asset_key,
                asset_type,
                status,
                description,
                json.dumps(metadata) if metadata else None,
                json.dumps(tags) if tags else None,
            )
            for asset_key in unique_keys
        ]

        requested_count = len(asset_keys)
        upsert_count = len(values)
        logger.info(
            "lineage_record_asset_nodes_started",
            requested_count=requested_count,
            upsert_count=upsert_count,
        )
        try:
            self._ensure_schema()
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    from psycopg2.extras import execute_values

                    execute_values(
                        cur,
                        """
                        INSERT INTO phlo.asset_lineage_nodes
                        (asset_key, asset_type, status, description, metadata, tags)
                        VALUES %s
                        ON CONFLICT (asset_key) DO UPDATE SET
                            asset_type = COALESCE(EXCLUDED.asset_type, phlo.asset_lineage_nodes.asset_type),
                            status = COALESCE(EXCLUDED.status, phlo.asset_lineage_nodes.status),
                            description = COALESCE(
                                EXCLUDED.description, phlo.asset_lineage_nodes.description
                            ),
                            metadata = COALESCE(EXCLUDED.metadata, phlo.asset_lineage_nodes.metadata),
                            tags = COALESCE(EXCLUDED.tags, phlo.asset_lineage_nodes.tags),
                            updated_at = NOW()
                        """,
                        values,
                    )
                conn.commit()
            logger.info(
                "lineage_record_asset_nodes_succeeded",
                requested_count=requested_count,
                upsert_count=upsert_count,
            )
        except Exception:
            logger.warning(
                "lineage_record_asset_nodes_failed",
                requested_count=requested_count,
                upsert_count=upsert_count,
                exc_info=True,
            )
            raise

        return len(values)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;asset_keys&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
      List of unique asset identifiers (e.g., "bronze.orders",
      "silver.stg\_orders").
    </PyParameter>

    <PyParameter name="&#x22;asset_type&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Classification of the asset. Common values:

      * "ingestion": Raw loaded data
      * "transform": dbt model or transformation output
      * "publish": Final published dataset
    </PyParameter>

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Current status of the asset:

      * "success": Successfully materialized
      * "warning": Completed with warnings
      * "failure": Failed or stale
      * "unknown": Status not determined
    </PyParameter>

    <PyParameter name="&#x22;description&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Human-readable description of the asset.
    </PyParameter>

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      JSON-serializable dictionary with arbitrary asset metadata.
    </PyParameter>

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Dictionary of string tags for categorization and filtering.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;">
    Number of asset nodes successfully persisted.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;record_asset_edges&#x22;" type="&#x22;(self, edges, *, asset_keys=None, metadata=None, tags=None) -> int&#x22;">
  Record directed edges between assets in the lineage graph.

  Creates or updates lineage edges representing data dependencies (source
  -> target). Also creates/updates node entries for all assets mentioned
  in edges or the explicit asset\_keys list.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > edges = \[
    > > > ...     ("bronze.orders", "silver.stg\_orders"),
    > > > ...     ("silver.stg\_orders", "gold.fct\_orders"),
    > > > ... ]
    > > > store.record\_asset\_edges(edges, metadata=\{"run\_id": "abc123"})
  </Callout>

  <Callout title="&#x22;Transaction Behavior&#x22;" type="&#x22;transaction-behavior&#x22;">
    Nodes are persisted before edges in the same logical operation,
    but there is no atomic transaction guarantee across the two calls.
    Edge records use UPSERT semantics with updated\_at refresh.
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    Edge persistence is skipped if the edges list is empty, but node
    creation still occurs if asset\_keys is provided.
  </Callout>

  <PySourceCode>
    ```python
    def record_asset_edges(
        self,
        edges: list[tuple[str, str]],
        *,
        asset_keys: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        tags: dict[str, Any] | None = None,
    ) -> int:
        """Record directed edges between assets in the lineage graph.

        Creates or updates lineage edges representing data dependencies (source
        -> target). Also creates/updates node entries for all assets mentioned
        in edges or the explicit asset_keys list.

        Args:
            edges: List of (source, target) tuples representing data flow
                direction (data flows from source to target).
            asset_keys: Optional additional asset keys to register as nodes
                even if not connected by edges.
            metadata: JSON-serializable dictionary for all edges in this batch.
            tags: Dictionary of string tags for all edges in this batch.

        Returns:
            Number of edges successfully persisted.

        Raises:
            Exception: Re-raised after logging if database operation fails.

        Example:
            >>> edges = [
            ...     ("bronze.orders", "silver.stg_orders"),
            ...     ("silver.stg_orders", "gold.fct_orders"),
            ... ]
            >>> store.record_asset_edges(edges, metadata={"run_id": "abc123"})

        Transaction Behavior:
            Nodes are persisted before edges in the same logical operation,
            but there is no atomic transaction guarantee across the two calls.
            Edge records use UPSERT semantics with updated_at refresh.

        Note:
            Edge persistence is skipped if the edges list is empty, but node
            creation still occurs if asset_keys is provided.

        """
        if not edges and not asset_keys:
            return 0

        edge_count = len(edges)
        explicit_asset_key_count = len(asset_keys or [])
        node_keys: set[str] = set(asset_keys or [])
        for source, target in edges:
            node_keys.add(source)
            node_keys.add(target)

        logger.info(
            "lineage_record_asset_edges_started",
            edge_count=edge_count,
            explicit_asset_key_count=explicit_asset_key_count,
            node_key_count=len(node_keys),
        )
        persisted_node_count = 0
        persisted_edge_count = 0
        try:
            if node_keys:
                persisted_node_count = self.record_asset_nodes(
                    list(node_keys),
                    metadata=metadata,
                    tags=tags,
                )

            if edges:
                values = [
                    (
                        source,
                        target,
                        json.dumps(metadata) if metadata else None,
                        json.dumps(tags) if tags else None,
                    )
                    for source, target in edges
                ]
                persisted_edge_count = len(values)
                self._ensure_schema()
                with psycopg2.connect(self.connection_string) as conn:
                    with conn.cursor() as cur:
                        from psycopg2.extras import execute_values

                        execute_values(
                            cur,
                            """
                            INSERT INTO phlo.asset_lineage_edges
                            (source_asset, target_asset, metadata, tags)
                            VALUES %s
                            ON CONFLICT (source_asset, target_asset) DO UPDATE SET
                                metadata = COALESCE(EXCLUDED.metadata, phlo.asset_lineage_edges.metadata),
                                tags = COALESCE(EXCLUDED.tags, phlo.asset_lineage_edges.tags),
                                updated_at = NOW()
                            """,
                            values,
                        )
                    conn.commit()
            logger.info(
                "lineage_record_asset_edges_succeeded",
                edge_count=edge_count,
                explicit_asset_key_count=explicit_asset_key_count,
                node_key_count=len(node_keys),
                persisted_node_count=persisted_node_count,
                persisted_edge_count=persisted_edge_count,
            )
        except Exception:
            logger.warning(
                "lineage_record_asset_edges_failed",
                edge_count=edge_count,
                explicit_asset_key_count=explicit_asset_key_count,
                node_key_count=len(node_keys),
                persisted_node_count=persisted_node_count,
                persisted_edge_count=persisted_edge_count,
                exc_info=True,
            )
            raise

        return persisted_edge_count
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;edges&#x22;" type="&#x22;list[tuple[str, str]]&#x22;" value="undefined">
      List of (source, target) tuples representing data flow
      direction (data flows from source to target).
    </PyParameter>

    <PyParameter name="&#x22;asset_keys&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      Optional additional asset keys to register as nodes
      even if not connected by edges.
    </PyParameter>

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      JSON-serializable dictionary for all edges in this batch.
    </PyParameter>

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Dictionary of string tags for all edges in this batch.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;">
    Number of edges successfully persisted.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;list_asset_nodes&#x22;" type="&#x22;(self) -> list[dict[str, Any]]&#x22;">
  List all asset nodes with their metadata.

  Queries the phlo.asset\_lineage\_nodes table and returns a list of
  dictionaries containing asset metadata.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > nodes = store.list\_asset\_nodes()
    > > > for node in nodes:
    > > > ...     print(f"\{node\['asset\_key']}: \{node\['status']}")
  </Callout>

  <PySourceCode>
    ```python
    def list_asset_nodes(self) -> list[dict[str, Any]]:
        """List all asset nodes with their metadata.

        Queries the phlo.asset_lineage_nodes table and returns a list of
        dictionaries containing asset metadata.

        Returns:
            List of dictionaries with keys:
                - asset_key: Unique identifier
                - asset_type: Classification (ingestion, transform, publish)
                - status: Current status (success, warning, failure, unknown)
                - description: Human-readable description
                - metadata: Parsed JSON metadata dict
                - tags: Parsed JSON tags dict
                - created_at: ISO format timestamp
                - updated_at: ISO format timestamp

        Example:
            >>> nodes = store.list_asset_nodes()
            >>> for node in nodes:
            ...     print(f"{node['asset_key']}: {node['status']}")

        """
        self._ensure_schema()
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT asset_key, asset_type, status, description, metadata, tags,
                           created_at, updated_at
                    FROM phlo.asset_lineage_nodes
                    """
                )
                rows = cur.fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "asset_key": row[0],
                    "asset_type": row[1],
                    "status": row[2],
                    "description": row[3],
                    "metadata": row[4],
                    "tags": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "updated_at": row[7].isoformat() if row[7] else None,
                }
            )
        return results
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of dictionaries with keys:

    * asset\_key: Unique identifier
    * asset\_type: Classification (ingestion, transform, publish)
    * status: Current status (success, warning, failure, unknown)
    * description: Human-readable description
    * metadata: Parsed JSON metadata dict
    * tags: Parsed JSON tags dict
    * created\_at: ISO format timestamp
    * updated\_at: ISO format timestamp
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;list_asset_edges&#x22;" type="&#x22;(self) -> list[dict[str, Any]]&#x22;">
  List all directed edges in the lineage graph.

  Queries the phlo.asset\_lineage\_edges table and returns a list of
  dictionaries containing edge information.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > edges = store.list\_asset\_edges()
    > > > for edge in edges:
    > > > ...     print(f"\{edge\['source\_asset']} -> \{edge\['target\_asset']}")
  </Callout>

  <PySourceCode>
    ```python
    def list_asset_edges(self) -> list[dict[str, Any]]:
        """List all directed edges in the lineage graph.

        Queries the phlo.asset_lineage_edges table and returns a list of
        dictionaries containing edge information.

        Returns:
            List of dictionaries with keys:
                - source_asset: Upstream asset key
                - target_asset: Downstream asset key
                - metadata: Parsed JSON metadata dict
                - tags: Parsed JSON tags dict
                - created_at: ISO format timestamp
                - updated_at: ISO format timestamp

        Example:
            >>> edges = store.list_asset_edges()
            >>> for edge in edges:
            ...     print(f"{edge['source_asset']} -> {edge['target_asset']}")

        """
        self._ensure_schema()
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT source_asset, target_asset, metadata, tags, created_at, updated_at
                    FROM phlo.asset_lineage_edges
                    """
                )
                rows = cur.fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "source_asset": row[0],
                    "target_asset": row[1],
                    "metadata": row[2],
                    "tags": row[3],
                    "created_at": row[4].isoformat() if row[4] else None,
                    "updated_at": row[5].isoformat() if row[5] else None,
                }
            )
        return results
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of dictionaries with keys:

    * source\_asset: Upstream asset key
    * target\_asset: Downstream asset key
    * metadata: Parsed JSON metadata dict
    * tags: Parsed JSON tags dict
    * created\_at: ISO format timestamp
    * updated\_at: ISO format timestamp
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_row&#x22;" type="&#x22;(self, row_id) -> dict[str, Any] | None&#x22;">
  Retrieve lineage information for a single row by ID.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > row = store.get\_row("01ARZ3NDEKTSV4RRFFQ69G5FAV")
    > > > if row:
    > > > ...     print(f"Found in table: \{row\['table\_name']}")
  </Callout>

  <PySourceCode>
    ```python
    def get_row(self, row_id: str) -> dict[str, Any] | None:
        """Retrieve lineage information for a single row by ID.

        Args:
            row_id: ULID string identifier for the row.

        Returns:
            Dictionary with row lineage information if found, otherwise None.
            Dictionary keys:
                - row_id: The row ULID
                - table_name: Fully qualified table name
                - source_type: Origin classification
                - parent_row_ids: List of parent ULIDs
                - created_at: ISO format timestamp
                - metadata: Parsed JSON metadata dict

        Example:
            >>> row = store.get_row("01ARZ3NDEKTSV4RRFFQ69G5FAV")
            >>> if row:
            ...     print(f"Found in table: {row['table_name']}")

        """
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT row_id, table_name, source_type, parent_row_ids,
                           created_at, metadata
                    FROM phlo.row_lineage
                    WHERE row_id = %s
                    """,
                    (row_id,),
                )
                row = cur.fetchone()

        if not row:
            return None

        return {
            "row_id": row[0],
            "table_name": row[1],
            "source_type": row[2],
            "parent_row_ids": row[3] or [],
            "created_at": row[4].isoformat() if row[4] else None,
            "metadata": row[5],
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;row_id&#x22;" type="&#x22;str&#x22;" value="undefined">
      ULID string identifier for the row.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict[str, Any] | None&#x22;">
    Dictionary with row lineage information if found, otherwise None.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_ancestors&#x22;" type="&#x22;(self, row_id, max_depth=10) -> list[dict[str, Any]]&#x22;">
  Recursively retrieve all ancestor rows (upstream lineage).

  Uses a PostgreSQL recursive CTE to traverse parent relationships
  up to the specified maximum depth.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > ancestors = store.get\_ancestors("01ARZ3NDEKTSV4RRFFQ69G5FAV")
    > > > for ancestor in ancestors:
    > > > ...     print(f"Derived from: \{ancestor\['table\_name']}")
  </Callout>

  <Callout title="&#x22;Performance&#x22;" type="&#x22;performance&#x22;">
    Uses recursive CTE with DISTINCT to avoid duplicate rows when
    multiple paths converge on the same ancestor.
  </Callout>

  <PySourceCode>
    ```python
    def get_ancestors(self, row_id: str, max_depth: int = 10) -> list[dict[str, Any]]:
        """Recursively retrieve all ancestor rows (upstream lineage).

        Uses a PostgreSQL recursive CTE to traverse parent relationships
        up to the specified maximum depth.

        Args:
            row_id: ULID of the starting row to find ancestors for.
            max_depth: Maximum number of parent levels to traverse (default 10).
                Prevents infinite recursion in case of circular references.

        Returns:
            List of dictionaries containing ancestor row information, sorted by
            creation time descending (most recent first).

        Raises:
            Exception: If database query fails.

        Example:
            >>> ancestors = store.get_ancestors("01ARZ3NDEKTSV4RRFFQ69G5FAV")
            >>> for ancestor in ancestors:
            ...     print(f"Derived from: {ancestor['table_name']}")

        Performance:
            Uses recursive CTE with DISTINCT to avoid duplicate rows when
            multiple paths converge on the same ancestor.

        """
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH RECURSIVE ancestors AS (
                        -- Base case: get parents of the starting row
                        SELECT rl.row_id, rl.table_name, rl.source_type,
                               rl.parent_row_ids, rl.created_at, rl.metadata,
                               1 as depth
                        FROM phlo.row_lineage rl
                        WHERE rl.row_id = ANY(
                            SELECT unnest(parent_row_ids)
                            FROM phlo.row_lineage
                            WHERE row_id = %s
                        )

                        UNION ALL

                        -- Recursive case: get parents of parents
                        SELECT rl.row_id, rl.table_name, rl.source_type,
                               rl.parent_row_ids, rl.created_at, rl.metadata,
                               a.depth + 1
                        FROM phlo.row_lineage rl
                        INNER JOIN ancestors a
                            ON rl.row_id = ANY(a.parent_row_ids)
                        WHERE a.depth < %s
                    )
                    SELECT DISTINCT row_id, table_name, source_type,
                           parent_row_ids, created_at, metadata
                    FROM ancestors
                    ORDER BY created_at DESC
                    """,
                    (row_id, max_depth),
                )
                rows = cur.fetchall()

        return [
            {
                "row_id": row[0],
                "table_name": row[1],
                "source_type": row[2],
                "parent_row_ids": row[3] or [],
                "created_at": row[4].isoformat() if row[4] else None,
                "metadata": row[5],
            }
            for row in rows
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;row_id&#x22;" type="&#x22;str&#x22;" value="undefined">
      ULID of the starting row to find ancestors for.
    </PyParameter>

    <PyParameter name="&#x22;max_depth&#x22;" type="&#x22;int&#x22;" value="&#x22;10&#x22;">
      Maximum number of parent levels to traverse (default 10).
      Prevents infinite recursion in case of circular references.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of dictionaries containing ancestor row information, sorted by
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_descendants&#x22;" type="&#x22;(self, row_id, max_depth=10) -> list[dict[str, Any]]&#x22;">
  Recursively retrieve all descendant rows (downstream lineage).

  Uses a PostgreSQL recursive CTE to traverse child relationships
  (reverse parent lookup) up to the specified maximum depth.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > descendants = store.get\_descendants("01ARZ3NDEKTSV4RRFFQ69G5FAV")
    > > > for descendant in descendants:
    > > > ...     print(f"Used in: \{descendant\['table\_name']}")
  </Callout>

  <Callout title="&#x22;Performance&#x22;" type="&#x22;performance&#x22;">
    Uses recursive CTE with reverse index lookup (row\_id = ANY(parent\_row\_ids)).
    Ensure GIN index exists on parent\_row\_ids for large datasets.
  </Callout>

  <PySourceCode>
    ```python
    def get_descendants(self, row_id: str, max_depth: int = 10) -> list[dict[str, Any]]:
        """Recursively retrieve all descendant rows (downstream lineage).

        Uses a PostgreSQL recursive CTE to traverse child relationships
        (reverse parent lookup) up to the specified maximum depth.

        Args:
            row_id: ULID of the starting row to find descendants for.
            max_depth: Maximum number of child levels to traverse (default 10).
                Prevents infinite recursion in case of circular references.

        Returns:
            List of dictionaries containing descendant row information, sorted by
            creation time ascending (oldest first).

        Raises:
            Exception: If database query fails.

        Example:
            >>> descendants = store.get_descendants("01ARZ3NDEKTSV4RRFFQ69G5FAV")
            >>> for descendant in descendants:
            ...     print(f"Used in: {descendant['table_name']}")

        Performance:
            Uses recursive CTE with reverse index lookup (row_id = ANY(parent_row_ids)).
            Ensure GIN index exists on parent_row_ids for large datasets.

        """
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH RECURSIVE descendants AS (
                        -- Base case: find rows that have this row as parent
                        SELECT rl.row_id, rl.table_name, rl.source_type,
                               rl.parent_row_ids, rl.created_at, rl.metadata,
                               1 as depth
                        FROM phlo.row_lineage rl
                        WHERE %s = ANY(rl.parent_row_ids)

                        UNION ALL

                        -- Recursive case: find children of children
                        SELECT rl.row_id, rl.table_name, rl.source_type,
                               rl.parent_row_ids, rl.created_at, rl.metadata,
                               d.depth + 1
                        FROM phlo.row_lineage rl
                        INNER JOIN descendants d ON d.row_id = ANY(rl.parent_row_ids)
                        WHERE d.depth < %s
                    )
                    SELECT DISTINCT row_id, table_name, source_type,
                           parent_row_ids, created_at, metadata
                    FROM descendants
                    ORDER BY created_at ASC
                    """,
                    (row_id, max_depth),
                )
                rows = cur.fetchall()

        return [
            {
                "row_id": row[0],
                "table_name": row[1],
                "source_type": row[2],
                "parent_row_ids": row[3] or [],
                "created_at": row[4].isoformat() if row[4] else None,
                "metadata": row[5],
            }
            for row in rows
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;row_id&#x22;" type="&#x22;str&#x22;" value="undefined">
      ULID of the starting row to find descendants for.
    </PyParameter>

    <PyParameter name="&#x22;max_depth&#x22;" type="&#x22;int&#x22;" value="&#x22;10&#x22;">
      Maximum number of child levels to traverse (default 10).
      Prevents infinite recursion in case of circular references.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of dictionaries containing descendant row information, sorted by
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_table_rows&#x22;" type="&#x22;(self, table_name, limit=100) -> list[dict[str, Any]]&#x22;">
  Retrieve recent lineage records for a specific table.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > rows = store.get\_table\_rows("bronze.orders", limit=10)
    > > > print(f"Recent rows: \{len(rows)}")
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    This is a simple query without pagination. For large tables,
    consider adding offset or time-range filtering.
  </Callout>

  <PySourceCode>
    ```python
    def get_table_rows(self, table_name: str, limit: int = 100) -> list[dict[str, Any]]:
        """Retrieve recent lineage records for a specific table.

        Args:
            table_name: Fully qualified table name (e.g., "bronze.orders").
            limit: Maximum number of rows to return (default 100).

        Returns:
            List of row lineage dictionaries sorted by creation time descending
            (most recent first), limited to specified count.

        Example:
            >>> rows = store.get_table_rows("bronze.orders", limit=10)
            >>> print(f"Recent rows: {len(rows)}")

        Note:
            This is a simple query without pagination. For large tables,
            consider adding offset or time-range filtering.

        """
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT row_id, table_name, source_type, parent_row_ids,
                           created_at, metadata
                    FROM phlo.row_lineage
                    WHERE table_name = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (table_name, limit),
                )
                rows = cur.fetchall()

        return [
            {
                "row_id": row[0],
                "table_name": row[1],
                "source_type": row[2],
                "parent_row_ids": row[3] or [],
                "created_at": row[4].isoformat() if row[4] else None,
                "metadata": row[5],
            }
            for row in rows
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (e.g., "bronze.orders").
    </PyParameter>

    <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;100&#x22;">
      Maximum number of rows to return (default 100).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of row lineage dictionaries sorted by creation time descending
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;record_column_lineage&#x22;" type="&#x22;(self, mappings) -> int&#x22;">
  Batch-insert column lineage mappings.

  Persists column-to-column lineage relationships using efficient bulk
  insert via execute\_values. Duplicate mappings (same source/target asset
  and column combination) are silently skipped.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > from phlo\_lineage.store import ColumnLineage
    > > > mappings = \[
    > > > ...     ColumnLineage(
    > > > ...         source\_asset="bronze.orders",
    > > > ...         source\_column="order\_id",
    > > > ...         target\_asset="silver.stg\_orders",
    > > > ...         target\_column="order\_id",
    > > > ...     ),
    > > > ... ]
    > > > count = store.record\_column\_lineage(mappings)
  </Callout>

  <Callout title="&#x22;Performance&#x22;" type="&#x22;performance&#x22;">
    Uses psycopg2.extras.execute\_values for efficient bulk loading.
    Single round-trip regardless of batch size.
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    This method does not distinguish between new inserts and skipped
    duplicates in the return value. Use ON CONFLICT DO NOTHING behavior.
  </Callout>

  <PySourceCode>
    ```python
    def record_column_lineage(self, mappings: list[ColumnLineage]) -> int:
        """Batch-insert column lineage mappings.

        Persists column-to-column lineage relationships using efficient bulk
        insert via execute_values. Duplicate mappings (same source/target asset
        and column combination) are silently skipped.

        Args:
            mappings: List of ColumnLineage records to persist.

        Returns:
            Number of mappings submitted for insert (may differ from persisted
            count if duplicates exist).

        Raises:
            Exception: Re-raised after logging if batch insert fails.

        Example:
            >>> from phlo_lineage.store import ColumnLineage
            >>> mappings = [
            ...     ColumnLineage(
            ...         source_asset="bronze.orders",
            ...         source_column="order_id",
            ...         target_asset="silver.stg_orders",
            ...         target_column="order_id",
            ...     ),
            ... ]
            >>> count = store.record_column_lineage(mappings)

        Performance:
            Uses psycopg2.extras.execute_values for efficient bulk loading.
            Single round-trip regardless of batch size.

        Note:
            This method does not distinguish between new inserts and skipped
            duplicates in the return value. Use ON CONFLICT DO NOTHING behavior.

        """
        if not mappings:
            return 0

        values = [
            (
                m.source_asset,
                m.source_column,
                m.target_asset,
                m.target_column,
                m.source_type,
                json.dumps(m.metadata) if m.metadata else None,
            )
            for m in mappings
        ]

        logger.info("column_lineage_record_started", mapping_count=len(values))
        try:
            self._ensure_schema()
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    from psycopg2.extras import execute_values

                    execute_values(
                        cur,
                        """
                        INSERT INTO phlo.column_lineage
                        (source_asset, source_column, target_asset, target_column,
                         source_type, metadata)
                        VALUES %s
                        ON CONFLICT DO NOTHING
                        """,
                        values,
                    )
                conn.commit()
            logger.info("column_lineage_record_succeeded", mapping_count=len(values))
        except Exception:
            logger.warning(
                "column_lineage_record_failed",
                mapping_count=len(values),
                exc_info=True,
            )
            raise

        return len(values)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;mappings&#x22;" type="&#x22;list[ColumnLineage]&#x22;" value="undefined">
      List of ColumnLineage records to persist.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;">
    Number of mappings submitted for insert (may differ from persisted
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_upstream_columns&#x22;" type="&#x22;(self, target_asset, target_column=None) -> list[ColumnLineage]&#x22;">
  Query upstream column lineage for a target asset.

  Retrieves ColumnLineage records showing which upstream columns feed into
  the specified target asset and optionally a specific column.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > All upstream columns for the asset [#all-upstream-columns-for-the-asset]
    > > >
    > > > upstream = store.get\_upstream\_columns("silver.stg\_orders")
    > > >
    > > > Specific column only [#specific-column-only]
    > > >
    > > > upstream = store.get\_upstream\_columns("silver.stg\_orders", "order\_id")
  </Callout>

  <Callout title="&#x22;Query Pattern&#x22;" type="&#x22;query-pattern&#x22;">
    * Without target\_column: WHERE target\_asset = %s
    * With target\_column: WHERE target\_asset = %s AND target\_column = %s
  </Callout>

  <PySourceCode>
    ```python
    def get_upstream_columns(
        self,
        target_asset: str,
        target_column: str | None = None,
    ) -> list[ColumnLineage]:
        """Query upstream column lineage for a target asset.

        Retrieves ColumnLineage records showing which upstream columns feed into
        the specified target asset and optionally a specific column.

        Args:
            target_asset: Asset key of the downstream asset to query.
            target_column: Optional column name to narrow results. If None,
                returns lineage for all columns in the target asset.

        Returns:
            List of ColumnLineage records representing upstream dependencies.

        Example:
            >>> # All upstream columns for the asset
            >>> upstream = store.get_upstream_columns("silver.stg_orders")
            >>>
            >>> # Specific column only
            >>> upstream = store.get_upstream_columns("silver.stg_orders", "order_id")

        Query Pattern:
            - Without target_column: WHERE target_asset = %s
            - With target_column: WHERE target_asset = %s AND target_column = %s

        """
        self._ensure_schema()

        if target_column is not None:
            query = """
                SELECT source_asset, source_column, target_asset, target_column,
                       source_type, metadata
                FROM phlo.column_lineage
                WHERE target_asset = %s AND target_column = %s
            """
            params: tuple[str, ...] = (target_asset, target_column)
        else:
            query = """
                SELECT source_asset, source_column, target_asset, target_column,
                       source_type, metadata
                FROM phlo.column_lineage
                WHERE target_asset = %s
            """
            params = (target_asset,)

        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

        return [
            ColumnLineage(
                source_asset=r[0],
                source_column=r[1],
                target_asset=r[2],
                target_column=r[3],
                source_type=r[4],
                metadata=r[5],
            )
            for r in rows
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;target_asset&#x22;" type="&#x22;str&#x22;" value="undefined">
      Asset key of the downstream asset to query.
    </PyParameter>

    <PyParameter name="&#x22;target_column&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional column name to narrow results. If None,
      returns lineage for all columns in the target asset.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of ColumnLineage records representing upstream dependencies.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_downstream_columns&#x22;" type="&#x22;(self, source_asset, source_column=None) -> list[ColumnLineage]&#x22;">
  Query downstream column lineage for a source asset.

  Retrieves ColumnLineage records showing which downstream columns are
  derived from the specified source asset and optionally a specific column.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > All downstream columns for the asset [#all-downstream-columns-for-the-asset]
    > > >
    > > > downstream = store.get\_downstream\_columns("bronze.orders")
    > > >
    > > > Specific column only [#specific-column-only-1]
    > > >
    > > > downstream = store.get\_downstream\_columns("bronze.orders", "order\_id")
  </Callout>

  <Callout title="&#x22;Query Pattern&#x22;" type="&#x22;query-pattern&#x22;">
    * Without source\_column: WHERE source\_asset = %s
    * With source\_column: WHERE source\_asset = %s AND source\_column = %s
  </Callout>

  <PySourceCode>
    ```python
    def get_downstream_columns(
        self,
        source_asset: str,
        source_column: str | None = None,
    ) -> list[ColumnLineage]:
        """Query downstream column lineage for a source asset.

        Retrieves ColumnLineage records showing which downstream columns are
        derived from the specified source asset and optionally a specific column.

        Args:
            source_asset: Asset key of the upstream asset to query.
            source_column: Optional column name to narrow results. If None,
                returns lineage for all columns in the source asset.

        Returns:
            List of ColumnLineage records representing downstream dependents.

        Example:
            >>> # All downstream columns for the asset
            >>> downstream = store.get_downstream_columns("bronze.orders")
            >>>
            >>> # Specific column only
            >>> downstream = store.get_downstream_columns("bronze.orders", "order_id")

        Query Pattern:
            - Without source_column: WHERE source_asset = %s
            - With source_column: WHERE source_asset = %s AND source_column = %s

        """
        self._ensure_schema()

        if source_column is not None:
            query = """
                SELECT source_asset, source_column, target_asset, target_column,
                       source_type, metadata
                FROM phlo.column_lineage
                WHERE source_asset = %s AND source_column = %s
            """
            params: tuple[str, ...] = (source_asset, source_column)
        else:
            query = """
                SELECT source_asset, source_column, target_asset, target_column,
                       source_type, metadata
                FROM phlo.column_lineage
                WHERE source_asset = %s
            """
            params = (source_asset,)

        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

        return [
            ColumnLineage(
                source_asset=r[0],
                source_column=r[1],
                target_asset=r[2],
                target_column=r[3],
                source_type=r[4],
                metadata=r[5],
            )
            for r in rows
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source_asset&#x22;" type="&#x22;str&#x22;" value="undefined">
      Asset key of the upstream asset to query.
    </PyParameter>

    <PyParameter name="&#x22;source_column&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional column name to narrow results. If None,
      returns lineage for all columns in the source asset.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of ColumnLineage records representing downstream dependents.
  </PyFunctionReturn>
</PyFunction>
