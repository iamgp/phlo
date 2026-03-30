# NessieTableScanner (/docs/python-reference/packages/phlo-nessie/phlo_nessie/catalog_scanner/NessieTableScanner)



Scan Nessie Iceberg REST catalog for namespaces and tables.

Provides a lightweight client for catalog discovery operations against
the Nessie REST API. Supports fallback to Trino query engine when
direct Nessie API calls fail.

Attributes [#attributes]

<PyAttribute name="&#x22;nessie_uri&#x22;" type="null" value="&#x22;nessie_uri.rstrip('/')&#x22;">
  Base URI for Nessie Iceberg REST endpoint.
</PyAttribute>

<PyAttribute name="&#x22;timeout_seconds&#x22;" type="null" value="&#x22;timeout_seconds&#x22;">
  HTTP request timeout in seconds.
</PyAttribute>

<PyAttribute name="&#x22;_scan_fallback_used&#x22;" type="null" value="&#x22;False&#x22;">
  Flag indicating if Trino fallback was used.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, nessie_uri, timeout_seconds=30)&#x22;">
  Initialize scanner with Nessie base URI and request timeout.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > scanner = NessieTableScanner("[http://nessie:19120/iceberg](http://nessie:19120/iceberg)", timeout\_seconds=60)
  </Callout>

  <PySourceCode>
    ```python
    def __init__(self, nessie_uri: str, timeout_seconds: int = 30):
        """Initialize scanner with Nessie base URI and request timeout.

        Args:
            nessie_uri: Base URI for the Nessie Iceberg REST endpoint.
            timeout_seconds: HTTP request timeout in seconds.

        Example:
            >>> scanner = NessieTableScanner("http://nessie:19120/iceberg", timeout_seconds=60)

        """
        self.nessie_uri = nessie_uri.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._scan_fallback_used = False
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;nessie_uri&#x22;" type="&#x22;str&#x22;" value="undefined">
      Base URI for the Nessie Iceberg REST endpoint.
    </PyParameter>

    <PyParameter name="&#x22;timeout_seconds&#x22;" type="&#x22;int&#x22;" value="&#x22;30&#x22;">
      HTTP request timeout in seconds.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;from_config&#x22;" type="&#x22;(cls) -> NessieTableScanner&#x22;">
  Build a scanner using configured Nessie settings.

  <PySourceCode>
    ```python
    @classmethod
    def from_config(cls) -> NessieTableScanner:
        """Build a scanner using configured Nessie settings.

        Returns:
            NessieTableScanner: Configured scanner instance.

        """
        settings = get_settings()
        return cls(nessie_uri=settings.nessie_iceberg_rest_uri())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo_nessie.catalog_scanner.NessieTableScanner&#x22;">
    Configured scanner instance.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_request&#x22;" type="&#x22;(self, method, endpoint, params=None) -> Any&#x22;">
  Execute an HTTP request against Nessie and parse JSON response.

  <PySourceCode>
    ```python
    def _request(self, method: str, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Execute an HTTP request against Nessie and parse JSON response.

        Args:
            method: HTTP method.
            endpoint: Relative Nessie endpoint path.
            params: Optional query parameters.

        Returns:
            Any: Parsed JSON body, or empty dict when response body is empty.

        """
        url = f"{self.nessie_uri.rstrip('/')}/{endpoint.lstrip('/')}"
        response = requests.request(
            method=method,
            url=url,
            params=params,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json() if response.text else {}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;method&#x22;" type="&#x22;str&#x22;" value="undefined">
      HTTP method.
    </PyParameter>

    <PyParameter name="&#x22;endpoint&#x22;" type="&#x22;str&#x22;" value="undefined">
      Relative Nessie endpoint path.
    </PyParameter>

    <PyParameter name="&#x22;params&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Optional query parameters.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Parsed JSON body, or empty dict when response body is empty.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;list_namespaces&#x22;" type="&#x22;(self) -> list[dict[str, Any]]&#x22;">
  List namespaces (schemas) from Nessie.

  Retrieves all namespaces from the Nessie REST API. Falls back to
  Trino query engine if the direct API call fails with 404.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > scanner = NessieTableScanner.from\_config()
    > > > namespaces = scanner.list\_namespaces()
    > > > print(\[ns\['namespace'] for ns in namespaces])
    > > > \[\['raw'], \['bronze'], \['silver']]
  </Callout>

  <PySourceCode>
    ```python
    def list_namespaces(self) -> list[dict[str, Any]]:
        """List namespaces (schemas) from Nessie.

        Retrieves all namespaces from the Nessie REST API. Falls back to
        Trino query engine if the direct API call fails with 404.

        Returns:
            list[dict[str, Any]]: Namespace objects with 'namespace' key containing
                a list of namespace path components.

        Raises:
            requests.HTTPError: On API errors other than 404.

        Example:
            >>> scanner = NessieTableScanner.from_config()
            >>> namespaces = scanner.list_namespaces()
            >>> print([ns['namespace'] for ns in namespaces])
            [['raw'], ['bronze'], ['silver']]

        """
        try:
            data = self._request("GET", "/v1/namespaces")
        except requests.HTTPError as exc:
            response = getattr(exc, "response", None)
            if response is not None and response.status_code == 404:
                self._scan_fallback_used = True
                logger.warning(
                    "nessie_rest_namespace_list_fallback_to_trino",
                    nessie_uri=self.nessie_uri,
                )
                return self._list_namespaces_via_trino()
            raise
        namespaces = data.get("namespaces", [])
        if not isinstance(namespaces, list):
            return []
        normalized: list[dict[str, Any]] = []
        for entry in namespaces:
            if isinstance(entry, dict) and "namespace" in entry:
                normalized.append(entry)
            elif isinstance(entry, list) and all(isinstance(p, str) for p in entry):
                normalized.append({"namespace": entry})
            elif isinstance(entry, str):
                normalized.append({"namespace": [entry]})
        return normalized
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[dict\[str, Any]]: Namespace objects with 'namespace' key containing
    a list of namespace path components.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;list_tables_in_namespace&#x22;" type="&#x22;(self, namespace) -> list[dict[str, Any]]&#x22;">
  List all tables in a namespace.

  Retrieves table identifiers from a given namespace. Falls back to
  Trino query engine if the direct API call fails with 404.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > scanner = NessieTableScanner.from\_config()
    > > > tables = scanner.list\_tables\_in\_namespace("raw")
    > > > print(\[t\['name'] for t in tables])
    > > > \['customers', 'orders', 'products']
  </Callout>

  <PySourceCode>
    ```python
    def list_tables_in_namespace(self, namespace: str | list[str]) -> list[dict[str, Any]]:
        """List all tables in a namespace.

        Retrieves table identifiers from a given namespace. Falls back to
        Trino query engine if the direct API call fails with 404.

        Args:
            namespace: Namespace name as string or list of path components.

        Returns:
            list[dict[str, Any]]: Table objects with 'name' key.

        Raises:
            requests.HTTPError: On API errors other than 404.

        Example:
            >>> scanner = NessieTableScanner.from_config()
            >>> tables = scanner.list_tables_in_namespace("raw")
            >>> print([t['name'] for t in tables])
            ['customers', 'orders', 'products']

        """
        namespace_name = ".".join(namespace) if isinstance(namespace, list) else namespace
        try:
            data = self._request("GET", f"/v1/namespaces/{namespace_name}/tables")
        except requests.HTTPError as exc:
            response = getattr(exc, "response", None)
            if response is not None and response.status_code == 404:
                self._scan_fallback_used = True
                logger.warning(
                    "nessie_rest_table_list_fallback_to_trino",
                    namespace=namespace_name,
                    nessie_uri=self.nessie_uri,
                )
                return self._list_tables_via_trino(namespace_name)
            raise
        tables = data.get("tables")
        if isinstance(tables, list):
            return tables
        identifiers = data.get("identifiers")
        if isinstance(identifiers, list):
            normalized_tables = []
            for ident in identifiers:
                if isinstance(ident, dict) and isinstance(ident.get("name"), str):
                    normalized_tables.append({"name": ident["name"]})
            return normalized_tables
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;namespace&#x22;" type="&#x22;str | list[str]&#x22;" value="undefined">
      Namespace name as string or list of path components.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[dict\[str, Any]]: Table objects with 'name' key.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_table_metadata&#x22;" type="&#x22;(self, namespace, table_name) -> dict[str, Any] | None&#x22;">
  Fetch table metadata payload from Nessie.

  Retrieves complete table metadata including schema, partitioning,
  and properties. Falls back to Trino DESCRIBE if direct API fails.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > scanner = NessieTableScanner.from\_config()
    > > > meta = scanner.get\_table\_metadata("raw", "customers")
    > > > print(meta.get('schema', \{}).get('fields', \[]))
  </Callout>

  <PySourceCode>
    ```python
    def get_table_metadata(self, namespace: str, table_name: str) -> dict[str, Any] | None:
        """Fetch table metadata payload from Nessie.

        Retrieves complete table metadata including schema, partitioning,
        and properties. Falls back to Trino DESCRIBE if direct API fails.

        Args:
            namespace: Namespace containing the table.
            table_name: Table identifier name.

        Returns:
            dict[str, Any] | None: Normalized table metadata, or None if not found.

        Raises:
            requests.HTTPError: On API errors other than 404.

        Example:
            >>> scanner = NessieTableScanner.from_config()
            >>> meta = scanner.get_table_metadata("raw", "customers")
            >>> print(meta.get('schema', {}).get('fields', []))

        """
        try:
            data = self._request("GET", f"/v1/namespaces/{namespace}/tables/{table_name}")
            return self._normalize_table_metadata(table_name, data)
        except requests.HTTPError as e:
            response = getattr(e, "response", None)
            if response is not None and response.status_code == 404:
                metadata = self._get_table_metadata_via_trino(namespace, table_name)
                if metadata:
                    return metadata
                return None
            raise
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;namespace&#x22;" type="&#x22;str&#x22;" value="undefined">
      Namespace containing the table.
    </PyParameter>

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table identifier name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict[str, Any] | None&#x22;">
    dict\[str, Any] | None: Normalized table metadata, or None if not found.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_list_namespaces_via_trino&#x22;" type="&#x22;(self) -> list[dict[str, Any]]&#x22;">
  List namespaces using Trino as a fallback path.

  Falls back to Trino SHOW SCHEMAS when direct Nessie REST API
  returns 404 or is unavailable.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > namespaces = scanner.\_list\_namespaces\_via\_trino()
    > > > print(\[ns\['namespace'] for ns in namespaces])
  </Callout>

  <PySourceCode>
    ```python
    def _list_namespaces_via_trino(self) -> list[dict[str, Any]]:
        """List namespaces using Trino as a fallback path.

        Falls back to Trino SHOW SCHEMAS when direct Nessie REST API
        returns 404 or is unavailable.

        Returns:
            list[dict[str, Any]]: Namespace objects with ``namespace`` key.

        Example:
            >>> namespaces = scanner._list_namespaces_via_trino()
            >>> print([ns['namespace'] for ns in namespaces])

        """
        trino = self._get_query_engine()
        if trino is None:
            return []
        try:
            rows = trino.execute("SHOW SCHEMAS")
        except Exception as exc:  # noqa: BLE001 - log and return empty
            logger.warning(
                "nessie_trino_schema_list_failed",
                error=str(exc),
                exc_info=True,
            )
            return []
        namespaces = []
        for row in rows:
            if row and isinstance(row[0], str):
                namespaces.append({"namespace": [row[0]]})
        return namespaces
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[dict\[str, Any]]: Namespace objects with `namespace` key.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_list_tables_via_trino&#x22;" type="&#x22;(self, namespace) -> list[dict[str, Any]]&#x22;">
  List tables in a namespace using Trino as fallback.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > tables = scanner.\_list\_tables\_via\_trino("raw")
    > > > print(\[t\['name'] for t in tables])
  </Callout>

  <PySourceCode>
    ```python
    def _list_tables_via_trino(self, namespace: str) -> list[dict[str, Any]]:
        """List tables in a namespace using Trino as fallback.

        Args:
            namespace: Namespace to query.

        Returns:
            list[dict[str, Any]]: Table objects with ``name`` key.

        Example:
            >>> tables = scanner._list_tables_via_trino("raw")
            >>> print([t['name'] for t in tables])

        """
        trino = self._get_query_engine()
        if trino is None:
            return []
        try:
            rows = trino.execute(f"SHOW TABLES FROM {namespace}")
        except Exception as exc:  # noqa: BLE001 - log and return empty
            logger.warning(
                "nessie_trino_table_list_failed",
                namespace=namespace,
                error=str(exc),
                exc_info=True,
            )
            return []
        tables = []
        for row in rows:
            if row and isinstance(row[0], str):
                tables.append({"name": row[0]})
        return tables
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;namespace&#x22;" type="&#x22;str&#x22;" value="undefined">
      Namespace to query.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[dict\[str, Any]]: Table objects with `name` key.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_table_metadata_via_trino&#x22;" type="&#x22;(self, namespace, table_name) -> dict[str, Any] | None&#x22;">
  Fetch table metadata via Trino DESCRIBE fallback.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > meta = scanner.\_get\_table\_metadata\_via\_trino("raw", "customers")
    > > > print(meta.get('schema', \{}).get('fields', \[]))
  </Callout>

  <PySourceCode>
    ```python
    def _get_table_metadata_via_trino(
        self, namespace: str, table_name: str
    ) -> dict[str, Any] | None:
        """Fetch table metadata via Trino DESCRIBE fallback.

        Args:
            namespace: Namespace containing the table.
            table_name: Table identifier.

        Returns:
            dict[str, Any] | None: Normalized metadata when available.

        Example:
            >>> meta = scanner._get_table_metadata_via_trino("raw", "customers")
            >>> print(meta.get('schema', {}).get('fields', []))

        """
        trino = self._get_query_engine()
        if trino is None:
            return None
        try:
            rows = trino.execute(f"DESCRIBE {namespace}.{table_name}")
        except Exception as exc:  # noqa: BLE001 - log and return None
            logger.warning(
                "nessie_trino_describe_failed",
                namespace=namespace,
                table_name=table_name,
                error=str(exc),
                exc_info=True,
            )
            return None
        fields = []
        for row in rows:
            if not row:
                continue
            name = row[0] if isinstance(row[0], str) else None
            data_type = row[1] if len(row) > 1 and isinstance(row[1], str) else None
            if not name or not data_type:
                continue
            fields.append({"name": name, "type": data_type})
        if not fields:
            return None
        return {"name": table_name, "schema": {"fields": fields}}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;namespace&#x22;" type="&#x22;str&#x22;" value="undefined">
      Namespace containing the table.
    </PyParameter>

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table identifier.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict[str, Any] | None&#x22;">
    dict\[str, Any] | None: Normalized metadata when available.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_query_engine&#x22;" type="&#x22;(self) -> QueryEngine | None&#x22;">
  Return query engine used for fallback queries.

  Resolves the query engine capability from settings, returning
  None if no query engine is available.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > engine = scanner.\_get\_query\_engine()
    > > > if engine:
    > > > ...     result = engine.execute("SELECT 1")
  </Callout>

  <PySourceCode>
    ```python
    def _get_query_engine(self) -> QueryEngine | None:
        """Return query engine used for fallback queries.

        Resolves the query engine capability from settings, returning
        None if no query engine is available.

        Returns:
            QueryEngine | None: Query engine provider instance, or ``None`` when unavailable.

        Example:
            >>> engine = scanner._get_query_engine()
            >>> if engine:
            ...     result = engine.execute("SELECT 1")

        """
        query_engine_name = get_settings().nessie_query_engine
        resolution = resolve_capability("query_engine", query_engine_name)
        if resolution is None:
            logger.warning(
                "nessie_query_engine_unavailable",
                required_capability=(
                    f"query_engine:{query_engine_name}" if query_engine_name else "query_engine"
                ),
            )
            return None
        return resolution.provider
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;QueryEngine | None&#x22;">
    QueryEngine | None: Query engine provider instance, or `None` when unavailable.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_normalize_table_metadata&#x22;" type="&#x22;(self, table_name, data) -> dict[str, Any]&#x22;">
  Normalize Nessie table payload into a stable metadata shape.

  Handles various Nessie API response formats and extracts schema,
  location, and properties into a consistent structure.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > raw\_data = \{"metadata": \{"schema": \{"fields": \[...]}}}
    > > > normalized = scanner.\_normalize\_table\_metadata("customers", raw\_data)
    > > > print(normalized.get('schema'))
  </Callout>

  <PySourceCode>
    ```python
    def _normalize_table_metadata(self, table_name: str, data: Any) -> dict[str, Any]:
        """Normalize Nessie table payload into a stable metadata shape.

        Handles various Nessie API response formats and extracts schema,
        location, and properties into a consistent structure.

        Args:
            table_name: Table identifier.
            data: Raw response payload from Nessie.

        Returns:
            dict[str, Any]: Normalized metadata payload.

        Example:
            >>> raw_data = {"metadata": {"schema": {"fields": [...]}}}
            >>> normalized = scanner._normalize_table_metadata("customers", raw_data)
            >>> print(normalized.get('schema'))

        """
        if not isinstance(data, dict):
            return {"name": table_name}
        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            return data

        normalized: dict[str, Any] = {"name": table_name}

        schema = None
        if isinstance(metadata.get("schema"), dict):
            schema = metadata.get("schema")
        else:
            schemas = metadata.get("schemas")
            current_schema_id = metadata.get("current-schema-id")
            if isinstance(schemas, list):
                if isinstance(current_schema_id, int):
                    for entry in schemas:
                        if isinstance(entry, dict) and entry.get("schema-id") == current_schema_id:
                            schema = entry
                            break
                if schema is None and schemas:
                    first = schemas[0]
                    if isinstance(first, dict):
                        schema = first
        if isinstance(schema, dict) and isinstance(schema.get("fields"), list):
            normalized["schema"] = {"fields": schema.get("fields")}

        location = metadata.get("location")
        if isinstance(location, str):
            normalized["properties"] = {"location": location}

        if isinstance(metadata.get("properties"), dict) and "properties" not in normalized:
            normalized["properties"] = metadata.get("properties")

        return normalized
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table identifier.
    </PyParameter>

    <PyParameter name="&#x22;data&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Raw response payload from Nessie.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, Any]: Normalized metadata payload.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_catalog_ref_for_logs&#x22;" type="&#x22;(self) -> str | None&#x22;">
  Infer Nessie catalog ref from URI path when present.

  Parses the scanner's Nessie URI to extract the reference name
  (branch/tag) for logging purposes.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > scanner.nessie\_uri = "[http://nessie:19120/iceberg/main](http://nessie:19120/iceberg/main)"
    > > > ref = scanner.\_get\_catalog\_ref\_for\_logs()
    > > > 'main'
  </Callout>

  <PySourceCode>
    ```python
    def _get_catalog_ref_for_logs(self) -> str | None:
        """Infer Nessie catalog ref from URI path when present.

        Parses the scanner's Nessie URI to extract the reference name
        (branch/tag) for logging purposes.

        Returns:
            str | None: Catalog reference name, or None if not present in URI.

        Example:
            >>> scanner.nessie_uri = "http://nessie:19120/iceberg/main"
            >>> ref = scanner._get_catalog_ref_for_logs()
            'main'

        """
        path = urlparse(self.nessie_uri).path.rstrip("/")
        if not path:
            return None
        path_parts = [part for part in path.split("/") if part]
        if not path_parts:
            return None
        if path_parts[-1] == "iceberg":
            return None
        return path_parts[-1]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;">
    str | None: Catalog reference name, or None if not present in URI.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;scan_all_tables&#x22;" type="&#x22;(self) -> dict[str, list[dict[str, Any]]]&#x22;">
  Return mapping of namespace -> tables list from Nessie.

  Performs a complete catalog scan, discovering all namespaces and
  their tables. Tracks whether fallback to Trino was used during scan.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > scanner = NessieTableScanner.from\_config()
    > > > catalog = scanner.scan\_all\_tables()
    > > > for ns, tables in catalog.items():
    > > > ...     print(f"\{ns}: \{len(tables)} tables")
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    Check `scanner._scan_fallback_used` after scanning to determine
    if Trino fallback was required.
  </Callout>

  <PySourceCode>
    ```python
    def scan_all_tables(self) -> dict[str, list[dict[str, Any]]]:
        """Return mapping of namespace -> tables list from Nessie.

        Performs a complete catalog scan, discovering all namespaces and
        their tables. Tracks whether fallback to Trino was used during scan.

        Returns:
            dict[str, list[dict[str, Any]]]: Mapping of namespace names to
                lists of table metadata dictionaries.

        Raises:
            Exception: Propagates errors from underlying API calls.

        Example:
            >>> scanner = NessieTableScanner.from_config()
            >>> catalog = scanner.scan_all_tables()
            >>> for ns, tables in catalog.items():
            ...     print(f"{ns}: {len(tables)} tables")

        Note:
            Check `scanner._scan_fallback_used` after scanning to determine
            if Trino fallback was required.

        """
        self._scan_fallback_used = False
        catalog_ref = self._get_catalog_ref_for_logs()

        logger.info(
            "nessie_catalog_scan_all_tables_started",
            nessie_uri=self.nessie_uri,
            ref=catalog_ref,
        )

        catalog: dict[str, list[dict[str, Any]]] = {}
        namespace_count = 0
        table_count = 0
        try:
            for ns_obj in self.list_namespaces():
                ns_parts = ns_obj.get("namespace")
                if not isinstance(ns_parts, list) or not all(isinstance(p, str) for p in ns_parts):
                    continue
                ns_name = ".".join(ns_parts)
                tables = self.list_tables_in_namespace(ns_parts)
                catalog[ns_name] = tables
                namespace_count += 1
                table_count += len(tables)
        except Exception as exc:
            logger.error(
                "nessie_catalog_scan_all_tables_failed",
                nessie_uri=self.nessie_uri,
                ref=catalog_ref,
                namespace_count=namespace_count,
                table_count=table_count,
                fallback_used=self._scan_fallback_used,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise

        if self._scan_fallback_used:
            logger.warning(
                "nessie_catalog_scan_all_tables_fallback_used",
                nessie_uri=self.nessie_uri,
                ref=catalog_ref,
                namespace_count=namespace_count,
                table_count=table_count,
                fallback_used=True,
            )

        logger.info(
            "nessie_catalog_scan_all_tables_completed",
            nessie_uri=self.nessie_uri,
            ref=catalog_ref,
            namespace_count=namespace_count,
            table_count=table_count,
            fallback_used=self._scan_fallback_used,
        )
        return catalog
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, list\[dict\[str, Any]]]: Mapping of namespace names to
    lists of table metadata dictionaries.
  </PyFunctionReturn>
</PyFunction>
