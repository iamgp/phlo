# iceberg (/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/iceberg)



Iceberg Catalog API Router.

Endpoints for querying Iceberg tables via Trino.
Provides table listing, schema info, and metadata.

This module enables data exploration by exposing Iceberg table metadata
through Trino, including table listings, column schemas, row counts,
and storage metrics. Tables are classified by medallion layer (bronze,
silver, gold, publish) based on naming conventions.

Key Endpoints:
GET /tables: List all tables in the catalog.
GET /tables/\{table}/schema: Get column schema for a table.
GET /tables/\{table}/row-count: Get estimated row count.
GET /tables/\{table}/metadata: Get combined table metadata.

Environment Variables:
PHLO\_QUERY\_CATALOG: Default Trino catalog.
PHLO\_DEFAULT\_REF: Default schema/branch.

Example:
Listing tables in the warehouse:

.. code-block:: bash

curl "[http://localhost:4000/api/iceberg/tables?branch=main](http://localhost:4000/api/iceberg/tables?branch=main)"

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;router&#x22;" type="null" value="&#x22;APIRouter(tags=['iceberg'])&#x22;" />

<PyAttribute name="&#x22;CACHE_TTL_TABLES&#x22;" type="null" value="&#x22;60.0&#x22;" />

<PyAttribute name="&#x22;CACHE_TTL_SCHEMA&#x22;" type="null" value="&#x22;300.0&#x22;" />

<PyAttribute name="&#x22;Layer&#x22;" type="null" value="&#x22;Literal['bronze', 'silver', 'gold', 'publish', 'unknown']&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;IcebergTable&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/iceberg/IcebergTable&#x22;" />

      <Card title="&#x22;TableColumn&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/iceberg/TableColumn&#x22;" />

      <Card title="&#x22;TableMetadata&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/iceberg/TableMetadata&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_cache_get&#x22;" type="&#x22;(key, ttl) -> Any | None&#x22;">
      Get a cached value when still valid.

      <PySourceCode>
        ```python
        def _cache_get(key: str, ttl: float) -> Any | None:
            """Get a cached value when still valid.

            Args:
                key: Cache key.
                ttl: Time-to-live in seconds.

            Returns:
                Cached value or `None` when missing/expired.

            """
            entry = _cache.get(key)
            if not entry:
                return None
            timestamp, value = entry
            if time.time() - timestamp > ttl:
                _cache.pop(key, None)
                return None
            return value
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;key&#x22;" type="&#x22;str&#x22;" value="undefined">
          Cache key.
        </PyParameter>

        <PyParameter name="&#x22;ttl&#x22;" type="&#x22;float&#x22;" value="undefined">
          Time-to-live in seconds.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;Any | None&#x22;">
        Cached value or `None` when missing/expired.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_cache_set&#x22;" type="&#x22;(key, value) -> None&#x22;">
      Store a value in the in-memory cache.

      <PySourceCode>
        ```python
        def _cache_set(key: str, value: Any) -> None:
            """Store a value in the in-memory cache.

            Args:
                key: Cache key.
                value: Value to cache.

            """
            _cache[key] = (time.time(), value)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;key&#x22;" type="&#x22;str&#x22;" value="undefined">
          Cache key.
        </PyParameter>

        <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Value to cache.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;infer_layer&#x22;" type="&#x22;(name) -> Layer&#x22;">
      Infer data layer from table name.

      <PySourceCode>
        ```python
        def infer_layer(name: str) -> Layer:
            """Infer data layer from table name.

            Args:
                name: Table name.

            Returns:
                Inferred medallion layer.

            """
            lower = name.lower()
            # Bronze: raw ingestion tables from DLT
            if lower.startswith("dlt_"):
                return "bronze"
            # Silver: staged/cleaned tables
            if lower.startswith("stg_"):
                return "silver"
            # Gold: curated fact/dimension tables
            if lower.startswith("fct_") or lower.startswith("dim_"):
                return "gold"
            # Publish: mart tables for BI consumption
            if lower.startswith("mrt_") or lower.startswith("publish_"):
                return "publish"
            # Fallback checks
            if "raw" in lower:
                return "bronze"
            if "staging" in lower:
                return "silver"
            return "unknown"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Table name.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.observatory_api.iceberg.Layer&#x22;">
        Inferred medallion layer.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;infer_layer_from_schema&#x22;" type="&#x22;(schema, table_name) -> Layer&#x22;">
      Infer data layer from table and schema names.

      <PySourceCode>
        ```python
        def infer_layer_from_schema(schema: str, table_name: str) -> Layer:
            """Infer data layer from table and schema names.

            Args:
                schema: Schema name.
                table_name: Table name.

            Returns:
                Inferred medallion layer.

            """
            # First try table name (most reliable)
            from_table = infer_layer(table_name)
            if from_table != "unknown":
                return from_table

            # Fall back to schema name
            s = schema.lower()
            if s in ("bronze", "raw"):
                return "bronze"
            if s in ("silver", "staging"):
                return "silver"
            if s in ("gold", "curated"):
                return "gold"
            if s in ("publish", "marts"):
                return "publish"

            return "unknown"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
          Schema name.
        </PyParameter>

        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Table name.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.observatory_api.iceberg.Layer&#x22;">
        Inferred medallion layer.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;fetch_tables&#x22;" type="&#x22;(branch, catalog, schemas_to_query, trino_url, timeout_ms) -> list[IcebergTable] | dict[str, str]&#x22;">
      Fetch tables from known Iceberg schemas.

      <PySourceCode>
        ```python
        async def fetch_tables(
            branch: str | None,
            catalog: str,
            schemas_to_query: list[str],
            trino_url: str | None,
            timeout_ms: int,
        ) -> list[IcebergTable] | dict[str, str]:
            """Fetch tables from known Iceberg schemas.

            Args:
                branch: Branch/schema fallback name.
                catalog: Trino catalog name.
                schemas_to_query: Explicit schemas to query.
                trino_url: Optional Trino URL override.
                timeout_ms: Query timeout in milliseconds.

            Returns:
                Table list or an error dictionary.

            """
            all_tables: list[IcebergTable] = []
            seen_tables: set[str] = set()
            errors: list[str] = []

            for schema in schemas_to_query:
                sql = f"SHOW TABLES FROM {quote_identifier(catalog)}.{quote_identifier(schema)}"
                result = await execute_trino_query(sql, catalog, schema, trino_url, timeout_ms)

                if isinstance(result, QueryExecutionError):
                    errors.append(f"{schema}: {result.error}")
                    continue

                for row in result["rows"]:
                    table_name = row.get("Table") or row.get("table_name") or row.get("tableName")
                    if table_name and table_name not in seen_tables:
                        seen_tables.add(table_name)
                        all_tables.append(
                            IcebergTable(
                                catalog=catalog,
                                schema_name=schema,
                                name=table_name,
                                full_name=f"{quote_identifier(catalog)}.{quote_identifier(schema)}.{quote_identifier(table_name)}",
                                layer=infer_layer_from_schema(schema, table_name),
                            )
                        )

            # If no tables found in standard schemas, try branch as schema
            if not all_tables and errors and branch and branch not in schemas_to_query:
                # Try branch as the schema name
                sql = f"SHOW TABLES FROM {quote_identifier(catalog)}.{quote_identifier(branch)}"
                result = await execute_trino_query(sql, catalog, branch, trino_url, timeout_ms)

                if isinstance(result, QueryExecutionError):
                    return {"error": "; ".join(errors)}

                for row in result["rows"]:
                    table_name = row.get("Table") or row.get("table_name") or row.get("tableName")
                    if table_name:
                        all_tables.append(
                            IcebergTable(
                                catalog=catalog,
                                schema_name=branch,
                                name=table_name,
                                full_name=f"{quote_identifier(catalog)}.{quote_identifier(branch)}.{quote_identifier(table_name)}",
                                layer=infer_layer(table_name),
                            )
                        )

            if not all_tables and errors:
                return {"error": "; ".join(errors)}

            # Sort by layer then name
            layer_order = {"bronze": 0, "silver": 1, "gold": 2, "publish": 3, "unknown": 4}
            all_tables.sort(key=lambda t: (layer_order[t.layer], t.name))

            return all_tables
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;branch&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Branch/schema fallback name.
        </PyParameter>

        <PyParameter name="&#x22;catalog&#x22;" type="&#x22;str&#x22;" value="undefined">
          Trino catalog name.
        </PyParameter>

        <PyParameter name="&#x22;schemas_to_query&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
          Explicit schemas to query.
        </PyParameter>

        <PyParameter name="&#x22;trino_url&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Optional Trino URL override.
        </PyParameter>

        <PyParameter name="&#x22;timeout_ms&#x22;" type="&#x22;int&#x22;" value="undefined">
          Query timeout in milliseconds.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[IcebergTable] | dict[str, str]&#x22;">
        Table list or an error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;fetch_table_schema&#x22;" type="&#x22;(table, schema, catalog, trino_url=None, timeout_ms=30000) -> list[TableColumn] | dict[str, str]&#x22;">
      Fetch table columns from Trino.

      <PySourceCode>
        ```python
        async def fetch_table_schema(
            table: str,
            schema: str,
            catalog: str,
            trino_url: str | None = None,
            timeout_ms: int = 30000,
        ) -> list[TableColumn] | dict[str, str]:
            """Fetch table columns from Trino.

            Args:
                table: Table name.
                schema: Schema name.
                catalog: Trino catalog name.
                trino_url: Optional Trino URL override.
                timeout_ms: Query timeout in milliseconds.

            Returns:
                Column list or an error dictionary.

            """
            sql = (
                f"DESCRIBE {quote_identifier(catalog)}.{quote_identifier(schema)}.{quote_identifier(table)}"
            )
            result = await execute_trino_query(sql, catalog, schema, trino_url, timeout_ms)

            if isinstance(result, QueryExecutionError):
                return {"error": result.error}

            columns = []
            for row in result["rows"]:
                col_name = row.get("Column") or row.get("column_name")
                col_type = row.get("Type") or row.get("data_type") or "unknown"
                extra = row.get("Extra") or ""
                comment = row.get("Comment") or None

                if col_name:
                    columns.append(
                        TableColumn(
                            name=col_name,
                            type=col_type,
                            nullable="NOT NULL" not in extra.upper() if extra else True,
                            comment=comment if comment else None,
                        )
                    )

            return columns
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
          Table name.
        </PyParameter>

        <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
          Schema name.
        </PyParameter>

        <PyParameter name="&#x22;catalog&#x22;" type="&#x22;str&#x22;" value="undefined">
          Trino catalog name.
        </PyParameter>

        <PyParameter name="&#x22;trino_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Trino URL override.
        </PyParameter>

        <PyParameter name="&#x22;timeout_ms&#x22;" type="&#x22;int&#x22;" value="&#x22;30000&#x22;">
          Query timeout in milliseconds.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[TableColumn] | dict[str, str]&#x22;">
        Column list or an error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_tables&#x22;" type="&#x22;(branch=None, catalog=None, preferred_schema=None, trino_url=None, timeout_ms=Query(default=30000, le=120000)) -> list[IcebergTable] | dict[str, str]&#x22;">
      Get tables from the Iceberg catalog.

      Discovers tables across configured schemas with optional caching.

      <PySourceCode>
        ```python
        @router.get("/tables", response_model=list[IcebergTable] | dict)
        async def get_tables(
            branch: str | None = None,
            catalog: str | None = None,
            preferred_schema: str | None = None,
            trino_url: str | None = None,
            timeout_ms: int = Query(default=30000, le=120000),
        ) -> list[IcebergTable] | dict[str, str]:
            """Get tables from the Iceberg catalog.

            Discovers tables across configured schemas with optional caching.

            Args:
                branch: Optional branch/schema fallback name.
                catalog: Optional Trino catalog override.
                preferred_schema: Optional schema to prioritize in discovery.
                trino_url: Optional Trino URL override.
                timeout_ms: Query timeout in milliseconds (default: 30000, max: 120000).

            Returns:
                List of IcebergTable objects, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            try:
                effective_catalog = catalog or resolve_default_catalog()
                effective_branch = branch
                schemas_to_query = resolve_table_discovery_schemas(preferred_schema, branch)
            except RuntimeError as exc:
                return {"error": str(exc)}

            cache_key = f"tables:{effective_catalog}:{effective_branch}:{','.join(schemas_to_query)}:{trino_url or 'default'}"
            cached = _cache_get(cache_key, CACHE_TTL_TABLES)
            if cached is not None:
                return cached

            result = await fetch_tables(
                effective_branch, effective_catalog, schemas_to_query, trino_url, timeout_ms
            )
            if not isinstance(result, dict):
                _cache_set(cache_key, result)
            return result
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;branch&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional branch/schema fallback name.
        </PyParameter>

        <PyParameter name="&#x22;catalog&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Trino catalog override.
        </PyParameter>

        <PyParameter name="&#x22;preferred_schema&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional schema to prioritize in discovery.
        </PyParameter>

        <PyParameter name="&#x22;trino_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Trino URL override.
        </PyParameter>

        <PyParameter name="&#x22;timeout_ms&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=30000, le=120000)&#x22;">
          Query timeout in milliseconds (default: 30000, max: 120000).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[IcebergTable] | dict[str, str]&#x22;">
        List of IcebergTable objects, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_table_schema&#x22;" type="&#x22;(table, schema=None, branch=None, catalog=None, trino_url=None, timeout_ms=Query(default=30000, le=120000)) -> list[TableColumn] | dict[str, str]&#x22;">
      Get table column schema.

      Returns column definitions with types, nullability, and comments.

      <PySourceCode>
        ```python
        @router.get("/tables/{table:path}/schema", response_model=list[TableColumn] | dict)
        async def get_table_schema(
            table: str,
            schema: str | None = None,
            branch: str | None = None,
            catalog: str | None = None,
            trino_url: str | None = None,
            timeout_ms: int = Query(default=30000, le=120000),
        ) -> list[TableColumn] | dict[str, str]:
            """Get table column schema.

            Returns column definitions with types, nullability, and comments.

            Args:
                table: Table name or fully qualified table path.
                schema: Optional schema override.
                branch: Optional default schema/branch.
                catalog: Optional Trino catalog override.
                trino_url: Optional Trino URL override.
                timeout_ms: Query timeout in milliseconds (default: 30000, max: 120000).

            Returns:
                List of TableColumn objects, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            try:
                effective_catalog = catalog or resolve_default_catalog()
                effective_schema = schema or branch or resolve_default_ref()
            except RuntimeError as exc:
                return {"error": str(exc)}

            cache_key = f"schema:{effective_catalog}:{effective_schema}:{table}:{trino_url or 'default'}"
            cached = _cache_get(cache_key, CACHE_TTL_SCHEMA)
            if cached is not None:
                return cached

            result = await fetch_table_schema(
                table, effective_schema, effective_catalog, trino_url, timeout_ms
            )
            if not isinstance(result, dict):
                _cache_set(cache_key, result)
            return result
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
          Table name or fully qualified table path.
        </PyParameter>

        <PyParameter name="&#x22;schema&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional schema override.
        </PyParameter>

        <PyParameter name="&#x22;branch&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional default schema/branch.
        </PyParameter>

        <PyParameter name="&#x22;catalog&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Trino catalog override.
        </PyParameter>

        <PyParameter name="&#x22;trino_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Trino URL override.
        </PyParameter>

        <PyParameter name="&#x22;timeout_ms&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=30000, le=120000)&#x22;">
          Query timeout in milliseconds (default: 30000, max: 120000).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[TableColumn] | dict[str, str]&#x22;">
        List of TableColumn objects, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_table_row_count&#x22;" type="&#x22;(table, branch=None, catalog=None, trino_url=None, timeout_ms=Query(default=30000, le=120000)) -> int | dict[str, str]&#x22;">
      Get row count for a table.

      Executes a COUNT(\*) query against the specified table.

      <PySourceCode>
        ```python
        @router.get("/tables/{table:path}/row-count", response_model=int | dict)
        async def get_table_row_count(
            table: str,
            branch: str | None = None,
            catalog: str | None = None,
            trino_url: str | None = None,
            timeout_ms: int = Query(default=30000, le=120000),
        ) -> int | dict[str, str]:
            """Get row count for a table.

            Executes a COUNT(*) query against the specified table.

            Args:
                table: Table name or fully qualified table path.
                branch: Optional schema/branch name.
                catalog: Optional Trino catalog override.
                trino_url: Optional Trino URL override.
                timeout_ms: Query timeout in milliseconds (default: 30000, max: 120000).

            Returns:
                Integer row count, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            try:
                effective_catalog = catalog or resolve_default_catalog()
                effective_branch = branch or resolve_default_ref()
            except RuntimeError as exc:
                return {"error": str(exc)}
            sql = f"SELECT COUNT(*) as cnt FROM {quote_identifier(effective_catalog)}.{quote_identifier(effective_branch)}.{quote_identifier(table)}"

            result = await execute_trino_query(
                sql, effective_catalog, effective_branch, trino_url, timeout_ms
            )

            if isinstance(result, QueryExecutionError):
                return {"error": result.error}

            if result["rows"]:
                return int(result["rows"][0].get("cnt", 0))
            return 0
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
          Table name or fully qualified table path.
        </PyParameter>

        <PyParameter name="&#x22;branch&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional schema/branch name.
        </PyParameter>

        <PyParameter name="&#x22;catalog&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Trino catalog override.
        </PyParameter>

        <PyParameter name="&#x22;trino_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Trino URL override.
        </PyParameter>

        <PyParameter name="&#x22;timeout_ms&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=30000, le=120000)&#x22;">
          Query timeout in milliseconds (default: 30000, max: 120000).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;int | dict[str, str]&#x22;">
        Integer row count, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_table_metadata&#x22;" type="&#x22;(table, branch=None, catalog=None, trino_url=None, timeout_ms=Query(default=30000, le=120000)) -> TableMetadata | dict[str, str]&#x22;">
      Get table metadata including schema and optional row count.

      Combines schema information with row count in a single response.

      <PySourceCode>
        ```python
        @router.get("/tables/{table:path}/metadata", response_model=TableMetadata | dict)
        async def get_table_metadata(
            table: str,
            branch: str | None = None,
            catalog: str | None = None,
            trino_url: str | None = None,
            timeout_ms: int = Query(default=30000, le=120000),
        ) -> TableMetadata | dict[str, str]:
            """Get table metadata including schema and optional row count.

            Combines schema information with row count in a single response.

            Args:
                table: Table name or fully qualified table path.
                branch: Optional schema/branch name.
                catalog: Optional Trino catalog override.
                trino_url: Optional Trino URL override.
                timeout_ms: Query timeout in milliseconds (default: 30000, max: 120000).

            Returns:
                TableMetadata with table info, columns, and row count, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            try:
                effective_catalog = catalog or resolve_default_catalog()
                effective_branch = branch or resolve_default_ref()
            except RuntimeError as exc:
                return {"error": str(exc)}

            # Get schema
            schema_result = await fetch_table_schema(
                table, effective_branch, effective_catalog, trino_url, timeout_ms
            )
            if isinstance(schema_result, dict) and "error" in schema_result:
                return schema_result

            # Get row count (optional)
            row_count = None
            try:
                count_result = await get_table_row_count(
                    table, effective_branch, effective_catalog, trino_url, timeout_ms
                )
                if isinstance(count_result, int):
                    row_count = count_result
            except Exception:
                pass  # Row count is optional

            return TableMetadata(
                table=IcebergTable(
                    catalog=effective_catalog,
                    schema_name=effective_branch,
                    name=table,
                    full_name=f"{quote_identifier(effective_catalog)}.{quote_identifier(effective_branch)}.{quote_identifier(table)}",
                    layer=infer_layer(table),
                ),
                columns=schema_result,  # type: ignore
                row_count=row_count,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
          Table name or fully qualified table path.
        </PyParameter>

        <PyParameter name="&#x22;branch&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional schema/branch name.
        </PyParameter>

        <PyParameter name="&#x22;catalog&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Trino catalog override.
        </PyParameter>

        <PyParameter name="&#x22;trino_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Trino URL override.
        </PyParameter>

        <PyParameter name="&#x22;timeout_ms&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=30000, le=120000)&#x22;">
          Query timeout in milliseconds (default: 30000, max: 120000).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;TableMetadata | dict[str, str]&#x22;">
        TableMetadata with table info, columns, and row count, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
