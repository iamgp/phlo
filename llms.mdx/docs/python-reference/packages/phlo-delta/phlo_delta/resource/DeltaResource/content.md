# DeltaResource (/docs/python-reference/packages/phlo-delta/phlo_delta/resource/DeltaResource)



Resource wrapper for Delta Lake table storage.

This class provides the primary interface for Delta Lake table operations
within the Phlo framework, implementing the table store protocol.

Functions [#functions]

<PyFunction name="&#x22;table_uri&#x22;" type="&#x22;(self, table_name) -> str&#x22;">
  Construct the full S3 path for a Delta table.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    uri = resource.table\_uri("raw\.events")

    Returns: "s3://lake/warehouse/delta/raw/events" [#returns-s3lakewarehousedeltarawevents]
  </Callout>

  <PySourceCode>
    ```python
    def table_uri(self, table_name: str) -> str:
        """Construct the full S3 path for a Delta table.

        Args:
            table_name: Fully qualified table name (namespace.table).

        Returns:
            str: S3 URI for the Delta table.

        Example:
            uri = resource.table_uri("raw.events")
            # Returns: "s3://lake/warehouse/delta/raw/events"

        """
        from phlo_delta.tables import _resolve_table_uri

        return _resolve_table_uri(table_name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (namespace.table).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    S3 URI for the Delta table.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_table&#x22;" type="&#x22;(self, table_name) -> Any&#x22;">
  Return a DeltaTable handle for the given table.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    table = resource.get\_table("raw\.events")
    version = table.version()
  </Callout>

  <PySourceCode>
    ```python
    def get_table(self, table_name: str) -> Any:
        """Return a DeltaTable handle for the given table.

        Args:
            table_name: Fully qualified table name (namespace.table).

        Returns:
            DeltaTable: Configured Delta table instance.

        Example:
            table = resource.get_table("raw.events")
            version = table.version()

        """
        from deltalake import DeltaTable

        from phlo_delta.tables import _resolve_table_uri

        table_uri = _resolve_table_uri(table_name)
        opts = get_settings().get_storage_options()
        return DeltaTable(table_uri, storage_options=opts)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (namespace.table).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Configured Delta table instance.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;schema_from_validation_schema&#x22;" type="&#x22;(self, validation_schema) -> pa.Schema&#x22;">
  Build a PyArrow schema from a validation model for ingestion flows.

  Converts a Pandera DataFrameModel to a PyArrow schema suitable for
  Delta Lake table creation.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    from my\_schemas import EventSchema
    schema = resource.schema\_from\_validation\_schema(EventSchema)
  </Callout>

  <PySourceCode>
    ```python
    def schema_from_validation_schema(
        self, validation_schema: type[DataFrameModel] | type[Any]
    ) -> pa.Schema:
        """Build a PyArrow schema from a validation model for ingestion flows.

        Converts a Pandera DataFrameModel to a PyArrow schema suitable for
        Delta Lake table creation.

        Args:
            validation_schema: Pandera DataFrameModel subclass defining the schema.

        Returns:
            pa.Schema: PyArrow schema equivalent to the validation model.

        Example:
            from my_schemas import EventSchema
            schema = resource.schema_from_validation_schema(EventSchema)

        """
        from phlo_delta.schema_conversion import pandera_to_delta

        return pandera_to_delta(validation_schema)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;validation_schema&#x22;" type="&#x22;type[DataFrameModel] | type[Any]&#x22;" value="undefined">
      Pandera DataFrameModel subclass defining the schema.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;pyarrow.Schema&#x22;">
    pa.Schema: PyArrow schema equivalent to the validation model.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;ensure_table&#x22;" type="&#x22;(self, table_name, schema, partition_spec=None, override_ref=None) -> Any&#x22;">
  Ensure a table exists and return its handle.

  Creates the table if it does not exist, or returns the existing table.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    table = resource.ensure\_table(
    "raw\.events",
    schema,
    partition\_spec=\[("date", "identity")]
    )
  </Callout>

  <PySourceCode>
    ```python
    def ensure_table(
        self,
        table_name: str,
        schema: pa.Schema,
        partition_spec: Sequence[tuple[str, str] | str] | None = None,
        override_ref: str | None = None,
    ) -> Any:
        """Ensure a table exists and return its handle.

        Creates the table if it does not exist, or returns the existing table.

        Args:
            table_name: Fully qualified table name (namespace.table).
            schema: PyArrow table schema.
            partition_spec: Optional shared partition specification.
            override_ref: Optional branch override for interface compatibility.

        Returns:
            DeltaTable: Existing or newly created Delta table.

        Raises:
            PhloConfigError: If an unsupported override_ref is provided.

        Example:
            table = resource.ensure_table(
                "raw.events",
                schema,
                partition_spec=[("date", "identity")]
            )

        """
        _resolve_delta_ref(override_ref)
        return ensure_table(
            table_name=table_name,
            schema=schema,
            partition_columns=_partition_columns_from_spec(partition_spec),
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (namespace.table).
    </PyParameter>

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;pa.Schema&#x22;" value="undefined">
      PyArrow table schema.
    </PyParameter>

    <PyParameter name="&#x22;partition_spec&#x22;" type="&#x22;Sequence[tuple[str, str] | str] | None&#x22;" value="&#x22;None&#x22;">
      Optional shared partition specification.
    </PyParameter>

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional branch override for interface compatibility.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Existing or newly created Delta table.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;append_parquet&#x22;" type="&#x22;(self, table_name, data_path, override_ref=None) -> dict[str, int]&#x22;">
  Append parquet data into a Delta table.

  Reads parquet data from the specified path and appends it to the table.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    result = resource.append\_parquet("raw\.events", "/data/events.parquet")
    print(f"Inserted \{result\['rows\_inserted']} rows")
  </Callout>

  <PySourceCode>
    ```python
    def append_parquet(
        self,
        table_name: str,
        data_path: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Append parquet data into a Delta table.

        Reads parquet data from the specified path and appends it to the table.

        Args:
            table_name: Fully qualified table name (namespace.table).
            data_path: Path to parquet input data.
            override_ref: Optional branch override for interface compatibility.

        Returns:
            dict[str, int]: Write statistics from the append operation,
                including rows_inserted and rows_deleted.

        Raises:
            PhloConfigError: If an unsupported override_ref is provided.
            Exception: If the append operation fails.

        Example:
            result = resource.append_parquet("raw.events", "/data/events.parquet")
            print(f"Inserted {result['rows_inserted']} rows")

        """
        _resolve_delta_ref(override_ref)
        logger.info(
            "delta_resource_append_requested",
            table_name=table_name,
            source=data_path,
        )
        try:
            result = append_to_table(table_name=table_name, data_path=data_path)
        except Exception as exc:
            logger.error(
                "delta_resource_append_failed",
                table_name=table_name,
                source=data_path,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "delta_resource_append_completed",
            table_name=table_name,
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
      Fully qualified table name (namespace.table).
    </PyParameter>

    <PyParameter name="&#x22;data_path&#x22;" type="&#x22;str&#x22;" value="undefined">
      Path to parquet input data.
    </PyParameter>

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional branch override for interface compatibility.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, int]: Write statistics from the append operation,
    including rows\_inserted and rows\_deleted.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;merge_parquet&#x22;" type="&#x22;(self, table_name, data_path, unique_key, override_ref=None) -> dict[str, int]&#x22;">
  Merge parquet data into a Delta table using a unique key.

  Performs an upsert operation: updates existing rows matching the unique key
  and inserts new rows.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    result = resource.merge\_parquet(
    "raw\.events", "/data/events.parquet", unique\_key="event\_id"
    )
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
        """Merge parquet data into a Delta table using a unique key.

        Performs an upsert operation: updates existing rows matching the unique key
        and inserts new rows.

        Args:
            table_name: Fully qualified table name (namespace.table).
            data_path: Path to parquet input data.
            unique_key: Column used to match existing rows.
            override_ref: Optional branch override for interface compatibility.

        Returns:
            dict[str, int]: Write statistics from the merge operation,
                including rows_inserted, rows_updated, and rows_deleted.

        Raises:
            PhloConfigError: If an unsupported override_ref is provided.
            Exception: If the merge operation fails.

        Example:
            result = resource.merge_parquet(
                "raw.events", "/data/events.parquet", unique_key="event_id"
            )

        """
        _resolve_delta_ref(override_ref)
        logger.info(
            "delta_resource_merge_requested",
            table_name=table_name,
            source=data_path,
            unique_key=unique_key,
        )
        try:
            result = merge_to_table(
                table_name=table_name,
                data_path=data_path,
                unique_key=unique_key,
            )
        except Exception as exc:
            logger.error(
                "delta_resource_merge_failed",
                table_name=table_name,
                source=data_path,
                unique_key=unique_key,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "delta_resource_merge_completed",
            table_name=table_name,
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
      Fully qualified table name (namespace.table).
    </PyParameter>

    <PyParameter name="&#x22;data_path&#x22;" type="&#x22;str&#x22;" value="undefined">
      Path to parquet input data.
    </PyParameter>

    <PyParameter name="&#x22;unique_key&#x22;" type="&#x22;str&#x22;" value="undefined">
      Column used to match existing rows.
    </PyParameter>

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional branch override for interface compatibility.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, int]: Write statistics from the merge operation,
    including rows\_inserted, rows\_updated, and rows\_deleted.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;overwrite_parquet&#x22;" type="&#x22;(self, *, table_name, data_path, override_ref=None) -> dict[str, int]&#x22;">
  Overwrite a Delta table with staged parquet data.

  Replaces all existing data in the table with the new parquet data.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    result = resource.overwrite\_parquet(
    table\_name="raw\.events",
    data\_path="/data/events.parquet"
    )
  </Callout>

  <PySourceCode>
    ```python
    def overwrite_parquet(
        self,
        *,
        table_name: str,
        data_path: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Overwrite a Delta table with staged parquet data.

        Replaces all existing data in the table with the new parquet data.

        Args:
            table_name: Fully qualified table name (namespace.table).
            data_path: Path to parquet input data.
            override_ref: Optional branch override for interface compatibility.

        Returns:
            dict[str, int]: Write statistics from the overwrite operation.

        Raises:
            PhloConfigError: If an unsupported override_ref is provided.
            Exception: If the overwrite operation fails.

        Example:
            result = resource.overwrite_parquet(
                table_name="raw.events",
                data_path="/data/events.parquet"
            )

        """
        _resolve_delta_ref(override_ref)
        logger.info(
            "delta_resource_overwrite_requested",
            table_name=table_name,
            source=data_path,
        )
        try:
            result = overwrite_table(table_name=table_name, data_path=data_path)
        except Exception as exc:
            logger.error(
                "delta_resource_overwrite_failed",
                table_name=table_name,
                source=data_path,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "delta_resource_overwrite_completed",
            table_name=table_name,
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
      Fully qualified table name (namespace.table).
    </PyParameter>

    <PyParameter name="&#x22;data_path&#x22;" type="&#x22;str&#x22;" value="undefined">
      Path to parquet input data.
    </PyParameter>

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional branch override for interface compatibility.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, int]: Write statistics from the overwrite operation.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;delete_rows&#x22;" type="&#x22;(self, *, table_name, predicate, override_ref=None) -> dict[str, int]&#x22;">
  Delete rows matching a predicate expression.

  Removes rows from the table that match the specified SQL predicate.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    result = resource.delete\_rows(
    table\_name="raw\.events",
    predicate="created\_at \< '2024-01-01'"
    )
  </Callout>

  <PySourceCode>
    ```python
    def delete_rows(
        self,
        *,
        table_name: str,
        predicate: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Delete rows matching a predicate expression.

        Removes rows from the table that match the specified SQL predicate.

        Args:
            table_name: Fully qualified table name (namespace.table).
            predicate: Filter expression (e.g. ``"status = 'inactive'"``).
            override_ref: Optional branch override for interface compatibility.

        Returns:
            dict[str, int]: Delete statistics (rows_deleted is -1 as Delta
                does not return a count from predicate deletes).

        Raises:
            PhloConfigError: If an unsupported override_ref is provided.
            Exception: If the delete operation fails.

        Example:
            result = resource.delete_rows(
                table_name="raw.events",
                predicate="created_at < '2024-01-01'"
            )

        """
        _resolve_delta_ref(override_ref)
        logger.info(
            "delta_resource_delete_rows_requested",
            table_name=table_name,
            predicate=predicate,
        )
        try:
            result = delete_rows_from_table(table_name=table_name, predicate=predicate)
        except Exception as exc:
            logger.error(
                "delta_resource_delete_rows_failed",
                table_name=table_name,
                predicate=predicate,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "delta_resource_delete_rows_completed",
            table_name=table_name,
            predicate=predicate,
        )
        return result
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (namespace.table).
    </PyParameter>

    <PyParameter name="&#x22;predicate&#x22;" type="&#x22;str&#x22;" value="undefined">
      Filter expression (e.g. `"status = 'inactive'"`).
    </PyParameter>

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional branch override for interface compatibility.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, int]: Delete statistics (rows\_deleted is -1 as Delta
    does not return a count from predicate deletes).
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;compact&#x22;" type="&#x22;(self, *, table_name) -> dict[str, object]&#x22;">
  Compact small files in a table using Delta OPTIMIZE.

  Runs the Delta OPTIMIZE command to coalesce small files into larger ones,
  improving query performance.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    result = resource.compact(table\_name="raw\.events")
    print(f"Compaction metrics: \{result\['compaction']}")
  </Callout>

  <PySourceCode>
    ```python
    def compact(self, *, table_name: str) -> dict[str, object]:
        """Compact small files in a table using Delta OPTIMIZE.

        Runs the Delta OPTIMIZE command to coalesce small files into larger ones,
        improving query performance.

        Args:
            table_name: Fully qualified table name (namespace.table).

        Returns:
            dict[str, object]: Compaction results from the optimize operation.

        Example:
            result = resource.compact(table_name="raw.events")
            print(f"Compaction metrics: {result['compaction']}")

        """
        from phlo_delta.tables import _resolve_table_uri

        table_uri = _resolve_table_uri(table_name)
        opts = get_settings().get_storage_options()
        delta_table_cls = _load_delta_table()

        logger.info("delta_resource_compact_requested", table_name=table_name)
        dt = delta_table_cls(table_uri, storage_options=opts)
        result = dt.optimize.compact()
        logger.info("delta_resource_compact_completed", table_name=table_name)
        return {"compaction": result}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (namespace.table).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, object]: Compaction results from the optimize operation.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;list_snapshots&#x22;" type="&#x22;(self, *, table_name, limit=10) -> list[dict]&#x22;">
  List recent table versions (Delta equivalent of snapshots).

  Retrieves the version history of the table, showing all changes over time.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    versions = resource.list\_snapshots(table\_name="raw\.events", limit=5)
    for v in versions:
    print(f"Version \{v\['version']}: \{v\['operation']}")
  </Callout>

  <PySourceCode>
    ```python
    def list_snapshots(self, *, table_name: str, limit: int = 10) -> list[dict]:
        """List recent table versions (Delta equivalent of snapshots).

        Retrieves the version history of the table, showing all changes over time.

        Args:
            table_name: Fully qualified table name (namespace.table).
            limit: Maximum number of versions to return (default: 10).

        Returns:
            list[dict]: Version metadata dicts, most recent first.
                Each dict contains version, timestamp, operation, and parameters.

        Example:
            versions = resource.list_snapshots(table_name="raw.events", limit=5)
            for v in versions:
                print(f"Version {v['version']}: {v['operation']}")

        """
        return list_table_versions(table_name=table_name, limit=limit)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (namespace.table).
    </PyParameter>

    <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;10&#x22;">
      Maximum number of versions to return (default: 10).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[dict]: Version metadata dicts, most recent first.
    Each dict contains version, timestamp, operation, and parameters.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;rollback_to_snapshot&#x22;" type="&#x22;(self, *, table_name, snapshot_id) -> dict&#x22;">
  Roll back a table to a previous version.

  Restores the table to a specific historical version using Delta's
  time travel capabilities.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    result = resource.rollback\_to\_snapshot(
    table\_name="raw\.events",
    snapshot\_id=42
    )
    print(f"Rolled back to version \{result\['rolled\_back\_to']}")
  </Callout>

  <PySourceCode>
    ```python
    def rollback_to_snapshot(self, *, table_name: str, snapshot_id: int | str) -> dict:
        """Roll back a table to a previous version.

        Restores the table to a specific historical version using Delta's
        time travel capabilities.

        Args:
            table_name: Fully qualified table name (namespace.table).
            snapshot_id: Target version number to restore to.

        Returns:
            dict: Contains ``rolled_back_to`` version number.

        Raises:
            Exception: If the rollback operation fails.

        Example:
            result = resource.rollback_to_snapshot(
                table_name="raw.events",
                snapshot_id=42
            )
            print(f"Rolled back to version {result['rolled_back_to']}")

        """
        logger.info(
            "delta_resource_rollback_requested",
            table_name=table_name,
            version=snapshot_id,
        )
        try:
            result = rollback_table_to_version(table_name=table_name, version=int(snapshot_id))
        except Exception as exc:
            logger.error(
                "delta_resource_rollback_failed",
                table_name=table_name,
                version=snapshot_id,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "delta_resource_rollback_completed",
            table_name=table_name,
            version=snapshot_id,
        )
        return result
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (namespace.table).
    </PyParameter>

    <PyParameter name="&#x22;snapshot_id&#x22;" type="&#x22;int | str&#x22;" value="undefined">
      Target version number to restore to.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Contains `rolled_back_to` version number.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;vacuum&#x22;" type="&#x22;(self, *, table_name, retain_hours=168) -> dict&#x22;">
  Remove old files via Delta vacuum.

  Deletes old data files that are no longer needed, based on the retention
  period. Default retention is 7 days (168 hours).

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    result = resource.vacuum(table\_name="raw\.events", retain\_hours=72)
    print(f"Removed \{result\['files\_removed']} files")
  </Callout>

  <PySourceCode>
    ```python
    def vacuum(self, *, table_name: str, retain_hours: int = 168) -> dict:
        """Remove old files via Delta vacuum.

        Deletes old data files that are no longer needed, based on the retention
        period. Default retention is 7 days (168 hours).

        Args:
            table_name: Fully qualified table name (namespace.table).
            retain_hours: Retention period in hours (default 168 = 7 days).

        Returns:
            dict: Vacuum results including files_removed count and removed_files list.

        Raises:
            Exception: If the vacuum operation fails.

        Example:
            result = resource.vacuum(table_name="raw.events", retain_hours=72)
            print(f"Removed {result['files_removed']} files")

        """
        logger.info(
            "delta_resource_vacuum_requested",
            table_name=table_name,
            retain_hours=retain_hours,
        )
        result = remove_orphan_files(table_name=table_name, retain_hours=retain_hours)
        logger.info(
            "delta_resource_vacuum_completed",
            table_name=table_name,
            files_removed=result["files_removed"],
        )
        return result
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (namespace.table).
    </PyParameter>

    <PyParameter name="&#x22;retain_hours&#x22;" type="&#x22;int&#x22;" value="&#x22;168&#x22;">
      Retention period in hours (default 168 = 7 days).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Vacuum results including files\_removed count and removed\_files list.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
