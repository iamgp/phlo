# HasuraClient (/docs/python-reference/packages/phlo-hasura/phlo_hasura/client/HasuraClient)



Client for Hasura Metadata API v1.

Provides methods for managing Hasura metadata including table tracking,
permissions, relationships, and metadata import/export. Handles URL
resolution and authentication automatically.

Attributes [#attributes]

<PyAttribute name="&#x22;hasura_url&#x22;" type="&#x22;str&#x22;" value="&#x22;_resolve_hasura_url(raw_url)&#x22;">
  Resolved Hasura GraphQL endpoint URL.
</PyAttribute>

<PyAttribute name="&#x22;admin_secret&#x22;" type="&#x22;str&#x22;" value="&#x22;admin_secret or os.environ.get('HASURA_ADMIN_SECRET', 'phlo-hasura-admin-secret')&#x22;">
  Admin secret for API authentication.
</PyAttribute>

<PyAttribute name="&#x22;metadata_url&#x22;" type="&#x22;str&#x22;" value="&#x22;f'{self.hasura_url}/v1/metadata'&#x22;">
  Full URL to the metadata API endpoint.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, hasura_url=None, admin_secret=None) -> None&#x22;">
  Initialize Hasura client.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > client = HasuraClient()
    > > > client = HasuraClient(
    > > > ...     hasura\_url="[http://custom:8080](http://custom:8080)",
    > > > ...     admin\_secret="my-secret"
    > > > ... )
  </Callout>

  <PySourceCode>
    ```python
    def __init__(self, hasura_url: str | None = None, admin_secret: str | None = None) -> None:
        """Initialize Hasura client.

        Args:
            hasura_url: Hasura GraphQL endpoint URL (default: http://hasura:8080).
                The URL will be resolved to handle Docker hostnames.
            admin_secret: Hasura admin secret (default: from HASURA_ADMIN_SECRET
                env var, or fallback to 'phlo-hasura-admin-secret').

        Example:
            >>> client = HasuraClient()
            >>> client = HasuraClient(
            ...     hasura_url="http://custom:8080",
            ...     admin_secret="my-secret"
            ... )

        """
        raw_url = hasura_url or "http://hasura:8080"
        self.hasura_url = _resolve_hasura_url(raw_url)
        self.admin_secret = admin_secret or os.environ.get(
            "HASURA_ADMIN_SECRET", "phlo-hasura-admin-secret"
        )
        self.metadata_url = f"{self.hasura_url}/v1/metadata"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;hasura_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Hasura GraphQL endpoint URL (default: [http://hasura:8080](http://hasura:8080)).
      The URL will be resolved to handle Docker hostnames.
    </PyParameter>

    <PyParameter name="&#x22;admin_secret&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Hasura admin secret (default: from HASURA\_ADMIN\_SECRET
      env var, or fallback to 'phlo-hasura-admin-secret').
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_request&#x22;" type="&#x22;(self, method, data, query_type=None) -> dict[str, Any]&#x22;">
  Make request to Hasura metadata API.

  Internal method for making authenticated requests to the Hasura
  metadata endpoint. Handles errors and provides structured logging.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > data = \{
    > > > ...     "type": "export\_metadata",
    > > > ...     "args": \{}
    > > > ... }
    > > > response = client.\_request("POST", data, "export\_metadata")
  </Callout>

  <PySourceCode>
    ```python
    def _request(
        self,
        method: str,
        data: dict[str, Any],
        query_type: str | None = None,
    ) -> dict[str, Any]:
        """Make request to Hasura metadata API.

        Internal method for making authenticated requests to the Hasura
        metadata endpoint. Handles errors and provides structured logging.

        Args:
            method: HTTP method (usually "POST" for metadata API).
            data: Request payload dictionary containing type and args.
            query_type: Type of query for error context and logging.

        Returns:
            Response JSON as dictionary.

        Raises:
            requests.RequestException: If the request fails or returns an error status.

        Example:
            >>> data = {
            ...     "type": "export_metadata",
            ...     "args": {}
            ... }
            >>> response = client._request("POST", data, "export_metadata")

        """
        headers = {
            "X-Hasura-Admin-Secret": self.admin_secret,
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(
                method, self.metadata_url, json=data, headers=headers, timeout=30
            )
        except requests.RequestException:
            logger.exception(
                "hasura_metadata_request_transport_failed",
                method=method,
                query_type=query_type or "unknown",
                metadata_url=self.metadata_url,
            )
            raise

        if response.status_code >= 400:
            error_msg = f"Hasura API error ({query_type}): {response.status_code}"
            logger.error(
                "hasura_metadata_request_failed",
                method=method,
                query_type=query_type or "unknown",
                metadata_url=self.metadata_url,
                status_code=response.status_code,
            )
            try:
                error_data = response.json()
                error_msg += f"\n{json.dumps(error_data, indent=2)}"
            except Exception:
                error_msg += f"\n{response.text}"
            raise requests.RequestException(error_msg)

        return response.json()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;method&#x22;" type="&#x22;str&#x22;" value="undefined">
      HTTP method (usually "POST" for metadata API).
    </PyParameter>

    <PyParameter name="&#x22;data&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Request payload dictionary containing type and args.
    </PyParameter>

    <PyParameter name="&#x22;query_type&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Type of query for error context and logging.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Response JSON as dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;track_table&#x22;" type="&#x22;(self, schema, table, alias=None) -> dict[str, Any]&#x22;">
  Track a table in Hasura.

  Registers a PostgreSQL table with Hasura so it becomes available
  through the GraphQL API. Optionally provides a custom alias for
  the root field names.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > client.track\_table("api", "orders")
    > > > client.track\_table("api", "order\_items", alias="line\_items")
  </Callout>

  <PySourceCode>
    ```python
    def track_table(self, schema: str, table: str, alias: str | None = None) -> dict[str, Any]:
        """Track a table in Hasura.

        Registers a PostgreSQL table with Hasura so it becomes available
        through the GraphQL API. Optionally provides a custom alias for
        the root field names.

        Args:
            schema: Schema name containing the table.
            table: Table name to track.
            alias: Optional alias for GraphQL type name (default: table name).
                When provided, custom root fields are configured.

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> client.track_table("api", "orders")
            >>> client.track_table("api", "order_items", alias="line_items")

        """
        config_dict: dict[str, Any] = {}
        if alias:
            config_dict = {
                "custom_root_fields": {},
                "custom_column_names": {},
            }

        data: dict[str, Any] = {
            "type": "pg_track_table",
            "args": {
                "schema": schema,
                "name": table,
                "configuration": config_dict,
            },
        }

        if alias and isinstance(data["args"], dict):
            config = data["args"].get("configuration")
            if isinstance(config, dict):
                config["custom_root_fields"] = {
                    "select": alias,
                    "select_by_pk": f"{alias}_by_pk",
                    "select_aggregate": f"{alias}_aggregate",
                }

        return self._request("POST", data, f"track_table({schema}.{table})")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name containing the table.
    </PyParameter>

    <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name to track.
    </PyParameter>

    <PyParameter name="&#x22;alias&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional alias for GraphQL type name (default: table name).
      When provided, custom root fields are configured.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    API response dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;untrack_table&#x22;" type="&#x22;(self, schema, table) -> dict[str, Any]&#x22;">
  Untrack a table from Hasura.

  Removes a previously tracked table from Hasura metadata, making it
  unavailable through the GraphQL API.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > client.untrack\_table("api", "old\_table")
  </Callout>

  <PySourceCode>
    ```python
    def untrack_table(self, schema: str, table: str) -> dict[str, Any]:
        """Untrack a table from Hasura.

        Removes a previously tracked table from Hasura metadata, making it
        unavailable through the GraphQL API.

        Args:
            schema: Schema name containing the table.
            table: Table name to untrack.

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> client.untrack_table("api", "old_table")

        """
        data = {
            "type": "pg_untrack_table",
            "args": {
                "schema": schema,
                "table": table,
            },
        }

        return self._request("POST", data, f"untrack_table({schema}.{table})")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name containing the table.
    </PyParameter>

    <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name to untrack.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    API response dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;create_select_permission&#x22;" type="&#x22;(self, schema, table, role, filter=None, columns=None) -> dict[str, Any]&#x22;">
  Create SELECT permission for a role on a table.

  Grants SELECT access to a specific role on a tracked table.
  Supports row-level security through filter expressions and
  column-level security through column lists.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > Allow anon to read all rows [#allow-anon-to-read-all-rows]
    > > >
    > > > client.create\_select\_permission("api", "orders", "anon")
    > > >
    > > > Allow users to read only their own orders [#allow-users-to-read-only-their-own-orders]
    > > >
    > > > client.create\_select\_permission(
    > > > ...     "api", "orders", "user",
    > > > ...     filter=\{"user\_id": \{"\_eq": "X-Hasura-User-Id"}},
    > > > ...     columns=\["id", "total", "status"]
    > > > ... )
  </Callout>

  <PySourceCode>
    ```python
    def create_select_permission(
        self,
        schema: str,
        table: str,
        role: str,
        filter: dict[str, Any] | None = None,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create SELECT permission for a role on a table.

        Grants SELECT access to a specific role on a tracked table.
        Supports row-level security through filter expressions and
        column-level security through column lists.

        Args:
            schema: Schema name containing the table.
            table: Table name to grant permissions on.
            role: Role name to grant permissions to.
            filter: Row-level security filter expression (default: {} for all rows).
            columns: Allowed columns list (default: ["*"] for all columns).

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> # Allow anon to read all rows
            >>> client.create_select_permission("api", "orders", "anon")
            >>> # Allow users to read only their own orders
            >>> client.create_select_permission(
            ...     "api", "orders", "user",
            ...     filter={"user_id": {"_eq": "X-Hasura-User-Id"}},
            ...     columns=["id", "total", "status"]
            ... )

        """
        if filter is None:
            filter = {}

        permission = {
            "columns": columns or ["*"],
            "filter": filter,
            "allow_aggregations": True,
        }

        data = {
            "type": "pg_create_select_permission",
            "args": {
                "schema": schema,
                "table": table,
                "role": role,
                "permission": permission,
            },
        }

        return self._request("POST", data, f"create_select_permission({schema}.{table}.{role})")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name containing the table.
    </PyParameter>

    <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name to grant permissions on.
    </PyParameter>

    <PyParameter name="&#x22;role&#x22;" type="&#x22;str&#x22;" value="undefined">
      Role name to grant permissions to.
    </PyParameter>

    <PyParameter name="&#x22;filter&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Row-level security filter expression (default: \{} for all rows).
    </PyParameter>

    <PyParameter name="&#x22;columns&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      Allowed columns list (default: \["\*"] for all columns).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    API response dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;create_insert_permission&#x22;" type="&#x22;(self, schema, table, role, check=None, columns=None, set=None) -> dict[str, Any]&#x22;">
  Create INSERT permission for a role on a table.

  Grants INSERT access to a specific role on a tracked table.
  Supports validation through check expressions and preset values
  that are automatically set on insert.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > client.create\_insert\_permission("api", "orders", "user")
    > > > client.create\_insert\_permission(
    > > > ...     "api", "orders", "user",
    > > > ...     check=\{"status": \{"\_eq": "pending"}},
    > > > ...     set=\{"created\_by": "x-hasura-user-id"}
    > > > ... )
  </Callout>

  <PySourceCode>
    ```python
    def create_insert_permission(
        self,
        schema: str,
        table: str,
        role: str,
        check: dict[str, Any] | None = None,
        columns: list[str] | None = None,
        set: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create INSERT permission for a role on a table.

        Grants INSERT access to a specific role on a tracked table.
        Supports validation through check expressions and preset values
        that are automatically set on insert.

        Args:
            schema: Schema name containing the table.
            table: Table name to grant permissions on.
            role: Role name to grant permissions to.
            check: Validation check expression (default: {} for no validation).
            columns: Allowed columns for insert (default: ["*"] for all).
            set: Preset values to automatically set on insert (e.g., {"created_by": "x-hasura-user-id"}).

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> client.create_insert_permission("api", "orders", "user")
            >>> client.create_insert_permission(
            ...     "api", "orders", "user",
            ...     check={"status": {"_eq": "pending"}},
            ...     set={"created_by": "x-hasura-user-id"}
            ... )

        """
        if check is None:
            check = {}

        permission = {
            "columns": columns or ["*"],
            "check": check,
        }

        if set:
            permission["set"] = set

        data = {
            "type": "pg_create_insert_permission",
            "args": {
                "schema": schema,
                "table": table,
                "role": role,
                "permission": permission,
            },
        }

        return self._request("POST", data, f"create_insert_permission({schema}.{table}.{role})")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name containing the table.
    </PyParameter>

    <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name to grant permissions on.
    </PyParameter>

    <PyParameter name="&#x22;role&#x22;" type="&#x22;str&#x22;" value="undefined">
      Role name to grant permissions to.
    </PyParameter>

    <PyParameter name="&#x22;check&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Validation check expression (default: \{} for no validation).
    </PyParameter>

    <PyParameter name="&#x22;columns&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      Allowed columns for insert (default: \["\*"] for all).
    </PyParameter>

    <PyParameter name="&#x22;set&#x22;" type="&#x22;dict[str, str] | None&#x22;" value="&#x22;None&#x22;">
      Preset values to automatically set on insert (e.g., \{"created\_by": "x-hasura-user-id"}).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    API response dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;drop_permission&#x22;" type="&#x22;(self, schema, table, role, permission_type='select') -> dict[str, Any]&#x22;">
  Drop a permission for a role.

  Removes a previously granted permission from a role on a table.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > client.drop\_permission("api", "orders", "anon", "select")
    > > > client.drop\_permission("api", "orders", "temp\_role", "insert")
  </Callout>

  <PySourceCode>
    ```python
    def drop_permission(
        self, schema: str, table: str, role: str, permission_type: str = "select"
    ) -> dict[str, Any]:
        """Drop a permission for a role.

        Removes a previously granted permission from a role on a table.

        Args:
            schema: Schema name containing the table.
            table: Table name to remove permissions from.
            role: Role name to remove permissions for.
            permission_type: Type of permission to drop. One of:
                'select', 'insert', 'update', or 'delete' (default: 'select').

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.
            KeyError: If an invalid permission_type is provided.

        Example:
            >>> client.drop_permission("api", "orders", "anon", "select")
            >>> client.drop_permission("api", "orders", "temp_role", "insert")

        """
        type_map = {
            "select": "pg_drop_select_permission",
            "insert": "pg_drop_insert_permission",
            "update": "pg_drop_update_permission",
            "delete": "pg_drop_delete_permission",
        }

        data = {
            "type": type_map[permission_type],
            "args": {
                "schema": schema,
                "table": table,
                "role": role,
            },
        }

        return self._request(
            "POST",
            data,
            f"drop_{permission_type}_permission({schema}.{table}.{role})",
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name containing the table.
    </PyParameter>

    <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name to remove permissions from.
    </PyParameter>

    <PyParameter name="&#x22;role&#x22;" type="&#x22;str&#x22;" value="undefined">
      Role name to remove permissions for.
    </PyParameter>

    <PyParameter name="&#x22;permission_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'select'&#x22;">
      Type of permission to drop. One of:
      'select', 'insert', 'update', or 'delete' (default: 'select').
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    API response dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;create_object_relationship&#x22;" type="&#x22;(self, schema, table, name, manual_configuration=None) -> dict[str, Any]&#x22;">
  Create object relationship (many-to-one).

  Creates a relationship where a single row in the source table
  relates to a single row in another table (e.g., order -> customer).

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > client.create\_object\_relationship(
    > > > ...     "api", "orders", "customer",
    > > > ...     manual\_configuration=\{"foreign\_key\_constraint\_on": "customer\_id"}
    > > > ... )
  </Callout>

  <PySourceCode>
    ```python
    def create_object_relationship(
        self,
        schema: str,
        table: str,
        name: str,
        manual_configuration: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create object relationship (many-to-one).

        Creates a relationship where a single row in the source table
        relates to a single row in another table (e.g., order -> customer).

        Args:
            schema: Schema name containing the source table.
            table: Source table name.
            name: Relationship name (e.g., "customer" for orders.customer).
            manual_configuration: Manual configuration dict specifying how to
                relate the tables. Typically contains 'foreign_key_constraint_on'
                with the column name.

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> client.create_object_relationship(
            ...     "api", "orders", "customer",
            ...     manual_configuration={"foreign_key_constraint_on": "customer_id"}
            ... )

        """
        data = {
            "type": "pg_create_object_relationship",
            "args": {
                "schema": schema,
                "table": table,
                "name": name,
                "using": manual_configuration or {},
            },
        }

        return self._request(
            "POST",
            data,
            f"create_object_relationship({schema}.{table}.{name})",
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name containing the source table.
    </PyParameter>

    <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
      Source table name.
    </PyParameter>

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Relationship name (e.g., "customer" for orders.customer).
    </PyParameter>

    <PyParameter name="&#x22;manual_configuration&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Manual configuration dict specifying how to
      relate the tables. Typically contains 'foreign\_key\_constraint\_on'
      with the column name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    API response dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;create_array_relationship&#x22;" type="&#x22;(self, schema, table, name, manual_configuration=None) -> dict[str, Any]&#x22;">
  Create array relationship (one-to-many).

  Creates a relationship where a single row in the source table
  relates to multiple rows in another table (e.g., customer -> orders).

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > client.create\_array\_relationship(
    > > > ...     "api", "customers", "orders",
    > > > ...     manual\_configuration=\{
    > > > ...         "foreign\_key\_constraint\_on": \{
    > > > ...             "table": "orders",
    > > > ...             "column": "customer\_id"
    > > > ...         }
    > > > ...     }
    > > > ... )
  </Callout>

  <PySourceCode>
    ```python
    def create_array_relationship(
        self,
        schema: str,
        table: str,
        name: str,
        manual_configuration: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create array relationship (one-to-many).

        Creates a relationship where a single row in the source table
        relates to multiple rows in another table (e.g., customer -> orders).

        Args:
            schema: Schema name containing the source table.
            table: Source table name.
            name: Relationship name (e.g., "orders" for customer.orders).
            manual_configuration: Manual configuration dict specifying how to
                relate the tables. Typically contains 'foreign_key_constraint_on'
                with table and column information.

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> client.create_array_relationship(
            ...     "api", "customers", "orders",
            ...     manual_configuration={
            ...         "foreign_key_constraint_on": {
            ...             "table": "orders",
            ...             "column": "customer_id"
            ...         }
            ...     }
            ... )

        """
        data = {
            "type": "pg_create_array_relationship",
            "args": {
                "schema": schema,
                "table": table,
                "name": name,
                "using": manual_configuration or {},
            },
        }

        return self._request(
            "POST",
            data,
            f"create_array_relationship({schema}.{table}.{name})",
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name containing the source table.
    </PyParameter>

    <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
      Source table name.
    </PyParameter>

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Relationship name (e.g., "orders" for customer.orders).
    </PyParameter>

    <PyParameter name="&#x22;manual_configuration&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Manual configuration dict specifying how to
      relate the tables. Typically contains 'foreign\_key\_constraint\_on'
      with table and column information.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    API response dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;export_metadata&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Export all Hasura metadata.

  Retrieves the complete Hasura metadata including tracked tables,
  relationships, permissions, event triggers, and remote schemas.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > metadata = client.export\_metadata()
    > > > len(metadata.get("sources", \[]))
    > > > 1
  </Callout>

  <PySourceCode>
    ```python
    def export_metadata(self) -> dict[str, Any]:
        """Export all Hasura metadata.

        Retrieves the complete Hasura metadata including tracked tables,
        relationships, permissions, event triggers, and remote schemas.

        Returns:
            Complete metadata dictionary containing:
                - version: Metadata format version
                - sources: Data sources and their tables
                - remote_schemas: Remote GraphQL schemas
                - actions: Custom actions
                - cron_triggers: Scheduled triggers
                - etc.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> metadata = client.export_metadata()
            >>> len(metadata.get("sources", []))
            1

        """
        data = {"type": "export_metadata", "args": {}}
        return self._request("POST", data, "export_metadata")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Complete metadata dictionary containing:

    * version: Metadata format version
    * sources: Data sources and their tables
    * remote\_schemas: Remote GraphQL schemas
    * actions: Custom actions
    * cron\_triggers: Scheduled triggers
    * etc.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;apply_metadata&#x22;" type="&#x22;(self, metadata) -> dict[str, Any]&#x22;">
  Apply metadata to Hasura.

  Replaces the current Hasura metadata with the provided metadata
  dictionary. This is a destructive operation that will remove
  any existing metadata not present in the input.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > metadata = client.export\_metadata()
    > > >
    > > > Modify metadata... [#modify-metadata]
    > > >
    > > > response = client.apply\_metadata(metadata)
  </Callout>

  <PySourceCode>
    ```python
    def apply_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Apply metadata to Hasura.

        Replaces the current Hasura metadata with the provided metadata
        dictionary. This is a destructive operation that will remove
        any existing metadata not present in the input.

        Args:
            metadata: Complete metadata dictionary to apply.

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> metadata = client.export_metadata()
            >>> # Modify metadata...
            >>> response = client.apply_metadata(metadata)

        """
        data = {"type": "replace_metadata", "args": {"metadata": metadata}}
        return self._request("POST", data, "apply_metadata")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Complete metadata dictionary to apply.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    API response dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;reload_metadata&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Reload metadata from database.

  Forces Hasura to reload its metadata from the underlying database.
  Useful when database schema changes occur outside of Hasura.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > client.reload\_metadata()  # After manual DB schema changes
  </Callout>

  <PySourceCode>
    ```python
    def reload_metadata(self) -> dict[str, Any]:
        """Reload metadata from database.

        Forces Hasura to reload its metadata from the underlying database.
        Useful when database schema changes occur outside of Hasura.

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> client.reload_metadata()  # After manual DB schema changes

        """
        data = {"type": "reload_metadata", "args": {}}
        return self._request("POST", data, "reload_metadata")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    API response dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_tables&#x22;" type="&#x22;(self, schema) -> list[str]&#x22;">
  Get list of tables in a schema.

  Queries the current metadata to find all tracked tables
  within a specific schema.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > tables = client.get\_tables("api")
    > > > print(tables)
    > > > \['orders', 'customers', 'products']
  </Callout>

  <PySourceCode>
    ```python
    def get_tables(self, schema: str) -> list[str]:
        """Get list of tables in a schema.

        Queries the current metadata to find all tracked tables
        within a specific schema.

        Args:
            schema: Schema name to query.

        Returns:
            List of table names tracked in the specified schema.

        Example:
            >>> tables = client.get_tables("api")
            >>> print(tables)
            ['orders', 'customers', 'products']

        """
        metadata = self.export_metadata()

        tables = []
        for source in metadata.get("sources", []):
            if source.get("name") == "default":
                for table in source.get("tables", []):
                    if table.get("table", {}).get("schema") == schema:
                        tables.append(table["table"]["name"])

        return tables
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name to query.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of table names tracked in the specified schema.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_tracked_tables&#x22;" type="&#x22;(self) -> dict[str, list[str]]&#x22;">
  Get all tracked tables by schema.

  Returns a mapping of schema names to lists of tracked tables
  across all data sources in the metadata.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > tracked = client.get\_tracked\_tables()
    > > > for schema, tables in tracked.items():
    > > > ...     print(f"\{schema}: \{len(tables)} tables")
  </Callout>

  <PySourceCode>
    ```python
    def get_tracked_tables(self) -> dict[str, list[str]]:
        """Get all tracked tables by schema.

        Returns a mapping of schema names to lists of tracked tables
        across all data sources in the metadata.

        Returns:
            Dictionary mapping schema names to lists of table names.
            Example: {"api": ["orders", "customers"], "public": ["users"]}

        Example:
            >>> tracked = client.get_tracked_tables()
            >>> for schema, tables in tracked.items():
            ...     print(f"{schema}: {len(tables)} tables")

        """
        metadata = self.export_metadata()
        tracked = {}

        for source in metadata.get("sources", []):
            if source.get("name") == "default":
                for table in source.get("tables", []):
                    schema = table.get("table", {}).get("schema", "public")
                    table_name = table["table"]["name"]

                    if schema not in tracked:
                        tracked[schema] = []

                    tracked[schema].append(table_name)

        return tracked
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary mapping schema names to lists of table names.
  </PyFunctionReturn>
</PyFunction>
