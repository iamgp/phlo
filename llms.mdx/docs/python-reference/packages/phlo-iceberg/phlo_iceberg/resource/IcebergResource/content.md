# IcebergResource (/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/resource/IcebergResource)



Resource wrapper for Iceberg REST catalog operations.

Provides a high-level interface for common Iceberg table operations
including data ingestion (append, merge, overwrite), snapshot management,
and schema conversion. Designed for use as a Dagster resource.

Attributes [#attributes]

<PyAttribute name="&#x22;ref&#x22;" type="&#x22;str&#x22;" value="&#x22;field(default_factory=(lambda: get_settings().iceberg_default_ref))&#x22;">
  Nessie branch/tag reference for all operations. Defaults to
  the value from settings (typically `main`).
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_catalog&#x22;" type="&#x22;(self, override_ref=None) -> Catalog&#x22;">
  Return an Iceberg catalog client for the active branch.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Access catalog directly::

    iceberg = IcebergResource(ref="main")
    catalog = iceberg.get\_catalog()

    Access low-level catalog methods [#access-low-level-catalog-methods]

    table = catalog.load\_table("raw\.events")

    Or use different branch [#or-use-different-branch]

    dev\_catalog = iceberg.get\_catalog(override\_ref="dev-branch")
  </Callout>

  <PySourceCode>
    ```python
    def get_catalog(self, override_ref: str | None = None) -> Catalog:
        """Return an Iceberg catalog client for the active branch.

        Args:
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            Catalog: Configured PyIceberg catalog instance.

        Example:
            Access catalog directly::

                iceberg = IcebergResource(ref="main")
                catalog = iceberg.get_catalog()

                # Access low-level catalog methods
                table = catalog.load_table("raw.events")

                # Or use different branch
                dev_catalog = iceberg.get_catalog(override_ref="dev-branch")

        """
        branch = override_ref or self.ref
        return get_catalog(ref=branch)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional branch or tag to use instead of `self.ref`.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;pyiceberg.catalog.Catalog&#x22;">
    Configured PyIceberg catalog instance.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;schema_from_validation_schema&#x22;" type="&#x22;(self, validation_schema) -> Schema&#x22;">
  Convert a Pandera validation model to an Iceberg schema.

  Useful for ingestion flows where data is validated using Pandera
  models before being written to Iceberg.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Convert Pandera model to Iceberg schema::

    from pandera import DataFrameModel, Column, Int64, String

    class UserSchema(DataFrameModel):
    id: Column\[Int64]
    name: Column\[String]

    iceberg = IcebergResource()
    schema = iceberg.schema\_from\_validation\_schema(UserSchema)
    table = iceberg.ensure\_table("raw\.users", schema=schema)
  </Callout>

  <PySourceCode>
    ```python
    def schema_from_validation_schema(
        self, validation_schema: type[DataFrameModel] | type[Any]
    ) -> Schema:
        """Convert a Pandera validation model to an Iceberg schema.

        Useful for ingestion flows where data is validated using Pandera
        models before being written to Iceberg.

        Args:
            validation_schema: Pandera DataFrameModel class to convert.

        Returns:
            Schema: Iceberg schema equivalent to the Pandera model.

        Raises:
            SchemaConversionError: If the Pandera schema cannot be converted.

        Example:
            Convert Pandera model to Iceberg schema::

                from pandera import DataFrameModel, Column, Int64, String

                class UserSchema(DataFrameModel):
                    id: Column[Int64]
                    name: Column[String]

                iceberg = IcebergResource()
                schema = iceberg.schema_from_validation_schema(UserSchema)
                table = iceberg.ensure_table("raw.users", schema=schema)

        """
        from phlo_iceberg.schema_conversion import pandera_to_iceberg

        return pandera_to_iceberg(validation_schema)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;validation_schema&#x22;" type="&#x22;type[DataFrameModel] | type[Any]&#x22;" value="undefined">
      Pandera DataFrameModel class to convert.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;pyiceberg.schema.Schema&#x22;">
    Iceberg schema equivalent to the Pandera model.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;ensure_table&#x22;" type="&#x22;(self, table_name, schema, partition_spec=None, override_ref=None) -> Table&#x22;">
  Ensure a table exists and return its handle.

  Creates the table if it doesn't exist, otherwise returns the existing table.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Ensure table with partitioning::

    from pyiceberg.schema import Schema
    from pyiceberg.types import NestedField, LongType, TimestamptzType

    schema = Schema(
    NestedField(1, "id", LongType(), required=True),
    NestedField(2, "ts", TimestamptzType(), required=True),
    )

    table = iceberg.ensure\_table(
    "raw\.events",
    schema=schema,
    partition\_spec=\[("ts", "day")]
    )
  </Callout>

  <PySourceCode>
    ```python
    def ensure_table(
        self,
        table_name: str,
        schema: Schema,
        partition_spec: Sequence[tuple[str, str]] | None = None,
        override_ref: str | None = None,
    ) -> Table:
        """Ensure a table exists and return its handle.

        Creates the table if it doesn't exist, otherwise returns the existing table.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            schema: Iceberg table schema.
            partition_spec: Optional list of ``(field, transform)`` partition rules.
                Supported transforms: ``identity``, ``day``, ``hour``, ``month``, ``year``.
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            Table: Existing or newly created Iceberg table handle.

        Example:
            Ensure table with partitioning::

                from pyiceberg.schema import Schema
                from pyiceberg.types import NestedField, LongType, TimestamptzType

                schema = Schema(
                    NestedField(1, "id", LongType(), required=True),
                    NestedField(2, "ts", TimestamptzType(), required=True),
                )

                table = iceberg.ensure_table(
                    "raw.events",
                    schema=schema,
                    partition_spec=[("ts", "day")]
                )

        """
        branch = override_ref or self.ref
        return ensure_table(
            table_name=table_name,
            schema=schema,
            partition_spec=list(partition_spec) if partition_spec else None,
            ref=branch,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (`namespace.table`).
    </PyParameter>

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Schema&#x22;" value="undefined">
      Iceberg table schema.
    </PyParameter>

    <PyParameter name="&#x22;partition_spec&#x22;" type="&#x22;Sequence[tuple[str, str]] | None&#x22;" value="&#x22;None&#x22;">
      Optional list of `(field, transform)` partition rules.
      Supported transforms: `identity`, `day`, `hour`, `month`, `year`.
    </PyParameter>

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional branch or tag to use instead of `self.ref`.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;pyiceberg.table.Table&#x22;">
    Existing or newly created Iceberg table handle.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;append_parquet&#x22;" type="&#x22;(self, table_name, data_path, override_ref=None) -> dict[str, int]&#x22;">
  Append Parquet data into an Iceberg table.

  Reads data from a Parquet file or directory and appends it to the
  specified table. Automatically aligns schema and handles missing columns.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Simple append::

    result = iceberg.append\_parquet(
    table\_name="raw\.events",
    data\_path="/data/events\_2024-01-01.parquet"
    )

    Append to specific branch::

    result = iceberg.append\_parquet(
    table\_name="raw\.events",
    data\_path="/data/events.parquet",
    override\_ref="dev-branch"
    )
  </Callout>

  <PySourceCode>
    ```python
    def append_parquet(
        self, table_name: str, data_path: str, override_ref: str | None = None
    ) -> dict[str, int]:
        """Append Parquet data into an Iceberg table.

        Reads data from a Parquet file or directory and appends it to the
        specified table. Automatically aligns schema and handles missing columns.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            data_path: Path to Parquet input data (file or directory).
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Write statistics from the append operation:
                - ``rows_inserted``: Number of rows appended.
                - ``rows_deleted``: Always 0.

        Raises:
            Exception: Re-raises any errors during append.

        Example:
            Simple append::

                result = iceberg.append_parquet(
                    table_name="raw.events",
                    data_path="/data/events_2024-01-01.parquet"
                )

            Append to specific branch::

                result = iceberg.append_parquet(
                    table_name="raw.events",
                    data_path="/data/events.parquet",
                    override_ref="dev-branch"
                )

        """
        branch = override_ref or self.ref
        logger.info(
            "iceberg_resource_append_requested",
            table_name=table_name,
            ref=branch,
            source=data_path,
        )
        try:
            result = append_to_table(table_name=table_name, data_path=data_path, ref=branch)
        except Exception as exc:
            logger.error(
                "iceberg_resource_append_failed",
                table_name=table_name,
                ref=branch,
                source=data_path,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "iceberg_resource_append_completed",
            table_name=table_name,
            ref=branch,
            source=data_path,
            rows_inserted=result.get("rows_inserted", 0),
            rows_deleted=result.get("rows_deleted", 0),
        )
        return result
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (`namespace.table`).
    </PyParameter>

    <PyParameter name="&#x22;data_path&#x22;" type="&#x22;str&#x22;" value="undefined">
      Path to Parquet input data (file or directory).
    </PyParameter>

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional branch or tag to use instead of `self.ref`.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, int]: Write statistics from the append operation:

    * `rows_inserted`: Number of rows appended.
    * `rows_deleted`: Always 0.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;merge_parquet&#x22;" type="&#x22;(self, table_name, data_path, unique_key, override_ref=None) -> dict[str, int]&#x22;">
  Merge (upsert) Parquet data into an Iceberg table using a unique key.

  Deletes existing rows with matching unique key values, then inserts
  the new data. This implements an upsert pattern useful for
  idempotent data loads.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Upsert user data by ID::

    result = iceberg.merge\_parquet(
    table\_name="raw\.users",
    data\_path="/data/user\_updates.parquet",
    unique\_key="user\_id"
    )
    print(f"Updated \~\{result\['rows\_deleted']} rows")
    print(f"Inserted \{result\['rows\_inserted']} rows")
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    The `rows_deleted` count is an approximation because Iceberg
    doesn't report the actual number of rows deleted during the operation.
  </Callout>

  <PySourceCode>
    ```python
    def merge_parquet(
        self,
        table_name: str,
        data_path: str,
        unique_key: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Merge (upsert) Parquet data into an Iceberg table using a unique key.

        Deletes existing rows with matching unique key values, then inserts
        the new data. This implements an upsert pattern useful for
        idempotent data loads.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            data_path: Path to Parquet input data (file or directory).
            unique_key: Column name used to identify and match existing rows.
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Write statistics from the merge operation:
                - ``rows_deleted``: Approximate count of rows deleted.
                - ``rows_inserted``: Number of rows inserted.

        Raises:
            Exception: Re-raises any errors during merge.

        Example:
            Upsert user data by ID::

                result = iceberg.merge_parquet(
                    table_name="raw.users",
                    data_path="/data/user_updates.parquet",
                    unique_key="user_id"
                )
                print(f"Updated ~{result['rows_deleted']} rows")
                print(f"Inserted {result['rows_inserted']} rows")

        Note:
            The ``rows_deleted`` count is an approximation because Iceberg
            doesn't report the actual number of rows deleted during the operation.

        """
        branch = override_ref or self.ref
        logger.info(
            "iceberg_resource_merge_requested",
            table_name=table_name,
            ref=branch,
            source=data_path,
            unique_key=unique_key,
        )
        try:
            result = merge_to_table(
                table_name=table_name,
                data_path=data_path,
                unique_key=unique_key,
                ref=branch,
            )
        except Exception as exc:
            logger.error(
                "iceberg_resource_merge_failed",
                table_name=table_name,
                ref=branch,
                source=data_path,
                unique_key=unique_key,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "iceberg_resource_merge_completed",
            table_name=table_name,
            ref=branch,
            source=data_path,
            unique_key=unique_key,
            rows_inserted=result.get("rows_inserted", 0),
            rows_deleted=result.get("rows_deleted", 0),
        )
        return result
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (`namespace.table`).
    </PyParameter>

    <PyParameter name="&#x22;data_path&#x22;" type="&#x22;str&#x22;" value="undefined">
      Path to Parquet input data (file or directory).
    </PyParameter>

    <PyParameter name="&#x22;unique_key&#x22;" type="&#x22;str&#x22;" value="undefined">
      Column name used to identify and match existing rows.
    </PyParameter>

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional branch or tag to use instead of `self.ref`.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, int]: Write statistics from the merge operation:

    * `rows_deleted`: Approximate count of rows deleted.
    * `rows_inserted`: Number of rows inserted.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;overwrite_parquet&#x22;" type="&#x22;(self, *, table_name, data_path, override_ref=None) -> dict[str, int]&#x22;">
  Overwrite an Iceberg table with staged Parquet data.

  Replaces all existing data with the new data, creating a new snapshot.
  Previous data remains accessible via snapshot history until snapshots
  are expired.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Regenerate summary table::

    result = iceberg.overwrite\_parquet(
    table\_name="analytics.daily\_summary",
    data\_path="/data/regenerated\_summary.parquet"
    )
    print(f"Table now has \{result\['rows\_inserted']} rows")
  </Callout>

  <PySourceCode>
    ```python
    def overwrite_parquet(
        self, *, table_name: str, data_path: str, override_ref: str | None = None
    ) -> dict[str, int]:
        """Overwrite an Iceberg table with staged Parquet data.

        Replaces all existing data with the new data, creating a new snapshot.
        Previous data remains accessible via snapshot history until snapshots
        are expired.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            data_path: Path to Parquet input data (file or directory).
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Write statistics from the overwrite operation:
                - ``rows_inserted``: Number of rows in replacement data.
                - ``rows_deleted``: Always 0.

        Raises:
            Exception: Re-raises any errors during overwrite.

        Example:
            Regenerate summary table::

                result = iceberg.overwrite_parquet(
                    table_name="analytics.daily_summary",
                    data_path="/data/regenerated_summary.parquet"
                )
                print(f"Table now has {result['rows_inserted']} rows")

        """
        branch = override_ref or self.ref
        logger.info(
            "iceberg_resource_overwrite_requested",
            table_name=table_name,
            ref=branch,
            source=data_path,
        )
        try:
            result = overwrite_table(table_name=table_name, data_path=data_path, ref=branch)
        except Exception as exc:
            logger.error(
                "iceberg_resource_overwrite_failed",
                table_name=table_name,
                ref=branch,
                source=data_path,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "iceberg_resource_overwrite_completed",
            table_name=table_name,
            ref=branch,
            source=data_path,
            rows_inserted=result.get("rows_inserted", 0),
            rows_deleted=result.get("rows_deleted", 0),
        )
        return result
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (`namespace.table`).
    </PyParameter>

    <PyParameter name="&#x22;data_path&#x22;" type="&#x22;str&#x22;" value="undefined">
      Path to Parquet input data (file or directory).
    </PyParameter>

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional branch or tag to use instead of `self.ref`.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, int]: Write statistics from the overwrite operation:

    * `rows_inserted`: Number of rows in replacement data.
    * `rows_deleted`: Always 0.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;delete_rows&#x22;" type="&#x22;(self, *, table_name, predicate, override_ref=None) -> dict[str, int]&#x22;">
  Delete rows matching a predicate expression.

  Uses Iceberg's delete operation with a SQL-style predicate expression.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Delete old records::

    iceberg.delete\_rows(
    table\_name="raw\.events",
    predicate="event\_time \< '2024-01-01'"
    )

    Delete by status::

    iceberg.delete\_rows(
    table\_name="raw\.users",
    predicate="account\_status = 'deleted'"
    )
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    PyIceberg does not return the number of rows deleted, so
    `rows_deleted` is always -1.
  </Callout>

  <PySourceCode>
    ```python
    def delete_rows(
        self, *, table_name: str, predicate: str, override_ref: str | None = None
    ) -> dict[str, int]:
        """Delete rows matching a predicate expression.

        Uses Iceberg's delete operation with a SQL-style predicate expression.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            predicate: Filter expression string (e.g., ``"status = 'inactive'"``).
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Delete statistics:
                - ``rows_deleted``: Always -1 (PyIceberg doesn't return count).

        Raises:
            Exception: Re-raises any errors during deletion.

        Example:
            Delete old records::

                iceberg.delete_rows(
                    table_name="raw.events",
                    predicate="event_time < '2024-01-01'"
                )

            Delete by status::

                iceberg.delete_rows(
                    table_name="raw.users",
                    predicate="account_status = 'deleted'"
                )

        Note:
            PyIceberg does not return the number of rows deleted, so
            ``rows_deleted`` is always -1.

        """
        branch = override_ref or self.ref
        logger.info(
            "iceberg_resource_delete_rows_requested",
            table_name=table_name,
            ref=branch,
            predicate=predicate,
        )
        try:
            result = delete_rows_from_table(table_name=table_name, predicate=predicate, ref=branch)
        except Exception as exc:
            logger.error(
                "iceberg_resource_delete_rows_failed",
                table_name=table_name,
                ref=branch,
                predicate=predicate,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "iceberg_resource_delete_rows_completed",
            table_name=table_name,
            ref=branch,
            predicate=predicate,
        )
        return result
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (`namespace.table`).
    </PyParameter>

    <PyParameter name="&#x22;predicate&#x22;" type="&#x22;str&#x22;" value="undefined">
      Filter expression string (e.g., `"status = 'inactive'"`).
    </PyParameter>

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional branch or tag to use instead of `self.ref`.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, int]: Delete statistics:

    * `rows_deleted`: Always -1 (PyIceberg doesn't return count).
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;compact&#x22;" type="&#x22;(self, *, table_name, override_ref=None) -> dict[str, object]&#x22;">
  Compact small files in a table.

  <Callout title="&#x22;Warning&#x22;" type="&#x22;warning&#x22;">
    Not supported by PyIceberg directly. Use Trino `OPTIMIZE` command
    instead for file compaction.
  </Callout>

  <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
    Trino Iceberg connector: [https://trino.io/docs/current/connector/iceberg.html](https://trino.io/docs/current/connector/iceberg.html)
  </Callout>

  <PySourceCode>
    ```python
    def compact(self, *, table_name: str, override_ref: str | None = None) -> dict[str, object]:
        """Compact small files in a table.

        Warning:
            Not supported by PyIceberg directly. Use Trino ``OPTIMIZE`` command
            instead for file compaction.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Raises:
            NotImplementedError: Always raised. Use Trino for compaction.

        See Also:
            Trino Iceberg connector: https://trino.io/docs/current/connector/iceberg.html

        """
        raise NotImplementedError("Compaction requires Spark or Trino; use Trino OPTIMIZE instead")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (`namespace.table`).
    </PyParameter>

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional branch or tag to use instead of `self.ref`.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict[str, object]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_snapshots&#x22;" type="&#x22;(self, *, table_name, limit=10) -> list[dict]&#x22;">
  List recent table snapshots.

  Retrieves snapshot metadata including operation type, timestamp, and
  summary statistics. Results are sorted by timestamp (most recent first).

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Review table history::

    snapshots = iceberg.list\_snapshots(
    table\_name="raw\.events",
    limit=5
    )
    for snap in snapshots:
    print(f"\{snap\['snapshot\_id']}: \{snap\['operation']}")
  </Callout>

  <PySourceCode>
    ```python
    def list_snapshots(self, *, table_name: str, limit: int = 10) -> list[dict]:
        """List recent table snapshots.

        Retrieves snapshot metadata including operation type, timestamp, and
        summary statistics. Results are sorted by timestamp (most recent first).

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            limit: Maximum number of snapshots to return (default: 10).

        Returns:
            list[dict]: Snapshot metadata dicts, most recent first. Each dict
                contains ``snapshot_id``, ``timestamp_ms``, ``operation``, and
                ``summary`` fields.

        Example:
            Review table history::

                snapshots = iceberg.list_snapshots(
                    table_name="raw.events",
                    limit=5
                )
                for snap in snapshots:
                    print(f"{snap['snapshot_id']}: {snap['operation']}")

        """
        return list_table_snapshots(table_name=table_name, limit=limit, ref=self.ref)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (`namespace.table`).
    </PyParameter>

    <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;10&#x22;">
      Maximum number of snapshots to return (default: 10).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[dict]: Snapshot metadata dicts, most recent first. Each dict
    contains `snapshot_id`, `timestamp_ms`, `operation`, and
    `summary` fields.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;rollback_to_snapshot&#x22;" type="&#x22;(self, *, table_name, snapshot_id) -> dict&#x22;">
  Roll back a table to a previous snapshot.

  Restores the table to a specific point in time using the snapshot ID.
  Creates a new snapshot that points to the historical state.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Rollback after bad data load::

    Find snapshot to restore [#find-snapshot-to-restore]

    snapshots = iceberg.list\_snapshots(table\_name="raw\.events", limit=10)
    target\_id = snapshots\[1]\["snapshot\_id"]  # Previous snapshot

    Rollback [#rollback]

    result = iceberg.rollback\_to\_snapshot(
    table\_name="raw\.events",
    snapshot\_id=target\_id
    )
    print(f"Rolled back to snapshot \{result\['rolled\_back\_to']}")
  </Callout>

  <Callout title="&#x22;Warning&#x22;" type="&#x22;warning&#x22;">
    Rollback creates a new snapshot. The newer snapshots are not
    deleted and can still be accessed if needed.
  </Callout>

  <PySourceCode>
    ```python
    def rollback_to_snapshot(self, *, table_name: str, snapshot_id: int | str) -> dict:
        """Roll back a table to a previous snapshot.

        Restores the table to a specific point in time using the snapshot ID.
        Creates a new snapshot that points to the historical state.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            snapshot_id: Target snapshot ID (can be int or string).

        Returns:
            dict: Rollback result containing ``rolled_back_to`` snapshot ID.

        Raises:
            Exception: Re-raises any errors during rollback.

        Example:
            Rollback after bad data load::

                # Find snapshot to restore
                snapshots = iceberg.list_snapshots(table_name="raw.events", limit=10)
                target_id = snapshots[1]["snapshot_id"]  # Previous snapshot

                # Rollback
                result = iceberg.rollback_to_snapshot(
                    table_name="raw.events",
                    snapshot_id=target_id
                )
                print(f"Rolled back to snapshot {result['rolled_back_to']}")

        Warning:
            Rollback creates a new snapshot. The newer snapshots are not
            deleted and can still be accessed if needed.

        """
        logger.info(
            "iceberg_resource_rollback_requested",
            table_name=table_name,
            snapshot_id=snapshot_id,
        )
        try:
            result = rollback_table_to_snapshot(
                table_name=table_name, snapshot_id=int(snapshot_id), ref=self.ref
            )
        except Exception as exc:
            logger.error(
                "iceberg_resource_rollback_failed",
                table_name=table_name,
                snapshot_id=snapshot_id,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "iceberg_resource_rollback_completed",
            table_name=table_name,
            snapshot_id=snapshot_id,
        )
        return result
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (`namespace.table`).
    </PyParameter>

    <PyParameter name="&#x22;snapshot_id&#x22;" type="&#x22;int | str&#x22;" value="undefined">
      Target snapshot ID (can be int or string).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Rollback result containing `rolled_back_to` snapshot ID.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;vacuum&#x22;" type="&#x22;(self, *, table_name, retain_hours=168) -> dict&#x22;">
  Remove expired snapshots and orphan files.

  Performs table maintenance by:

  1. Expiring snapshots older than the retention period
  2. Removing orphan files not referenced by any remaining snapshot

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Weekly maintenance::

    result = iceberg.vacuum(
    table\_name="raw\.events",
    retain\_hours=168  # Keep 7 days
    )
    print(f"Removed \{result\['deleted\_snapshots']} snapshots")
    print(f"Removed \{result\['orphan\_files\_removed']} orphan files")
  </Callout>

  <Callout title="&#x22;Warning&#x22;" type="&#x22;warning&#x22;">
    Orphan file removal permanently deletes data files from storage.
    Ensure no concurrent writes are happening during vacuum operations.
  </Callout>

  <PySourceCode>
    ```python
    def vacuum(self, *, table_name: str, retain_hours: int = 168) -> dict:
        """Remove expired snapshots and orphan files.

        Performs table maintenance by:
        1. Expiring snapshots older than the retention period
        2. Removing orphan files not referenced by any remaining snapshot

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            retain_hours: Retention period in hours (default: 168 = 7 days).
                Snapshots newer than this will be retained.

        Returns:
            dict: Maintenance results containing:
                - ``deleted_snapshots``: Number of expired snapshots removed.
                - ``orphan_files_removed``: Number of orphan files deleted.

        Raises:
            Exception: Re-raises any errors during maintenance.

        Example:
            Weekly maintenance::

                result = iceberg.vacuum(
                    table_name="raw.events",
                    retain_hours=168  # Keep 7 days
                )
                print(f"Removed {result['deleted_snapshots']} snapshots")
                print(f"Removed {result['orphan_files_removed']} orphan files")

        Warning:
            Orphan file removal permanently deletes data files from storage.
            Ensure no concurrent writes are happening during vacuum operations.

        """
        logger.info(
            "iceberg_resource_vacuum_requested",
            table_name=table_name,
            retain_hours=retain_hours,
        )
        snap_result = expire_snapshots(
            table_name=table_name, older_than_hours=retain_hours, ref=self.ref
        )
        orphan_result = remove_orphan_files(
            table_name=table_name, older_than_hours=retain_hours, dry_run=False, ref=self.ref
        )
        result = {
            "deleted_snapshots": snap_result["deleted_snapshots"],
            "orphan_files_removed": orphan_result["orphan_count"],
        }
        logger.info(
            "iceberg_resource_vacuum_completed",
            table_name=table_name,
            **result,
        )
        return result
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (`namespace.table`).
    </PyParameter>

    <PyParameter name="&#x22;retain_hours&#x22;" type="&#x22;int&#x22;" value="&#x22;168&#x22;">
      Retention period in hours (default: 168 = 7 days).
      Snapshots newer than this will be retained.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Maintenance results containing:

    * `deleted_snapshots`: Number of expired snapshots removed.
    * `orphan_files_removed`: Number of orphan files deleted.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, ref=(lambda: get_settings().iceberg_default_ref)()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;ref&#x22;" type="&#x22;str&#x22;" value="&#x22;(lambda: get_settings().iceberg_default_ref)()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
