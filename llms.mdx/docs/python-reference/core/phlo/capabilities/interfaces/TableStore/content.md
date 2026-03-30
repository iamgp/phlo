# TableStore (/docs/python-reference/core/phlo/capabilities/interfaces/TableStore)



Protocol for table-store providers used by ingestion components.

Required methods: `ensure_table`, `append_parquet`, `merge_parquet`.
Extended operations (`overwrite_parquet`, `delete_rows`, `compact`,
`list_snapshots`, `rollback_to_snapshot`, `vacuum`) raise
`NotImplementedError` by default so providers opt in incrementally.

Functions [#functions]

<PyFunction name="&#x22;ensure_table&#x22;" type="&#x22;(self, *, table_name, schema, partition_spec=None, override_ref=None) -> Any&#x22;">
  Ensure a destination table exists.

  <PySourceCode>
    ```python
    def ensure_table(
        self,
        *,
        table_name: str,
        schema: Any,
        partition_spec: Any = None,
        override_ref: str | None = None,
    ) -> Any:
        """Ensure a destination table exists."""
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Any&#x22;" value="null" />

    <PyParameter name="&#x22;partition_spec&#x22;" type="&#x22;Any&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
</PyFunction>

<PyFunction name="&#x22;append_parquet&#x22;" type="&#x22;(self, *, table_name, data_path, override_ref=None) -> dict[str, int]&#x22;">
  Append staged parquet data to a destination table.

  <PySourceCode>
    ```python
    def append_parquet(
        self,
        *,
        table_name: str,
        data_path: str | Path,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Append staged parquet data to a destination table."""
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;data_path&#x22;" type="&#x22;str | Path&#x22;" value="null" />

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, int]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;merge_parquet&#x22;" type="&#x22;(self, *, table_name, data_path, unique_key, override_ref=None) -> dict[str, int]&#x22;">
  Merge staged parquet data into a destination table.

  <PySourceCode>
    ```python
    def merge_parquet(
        self,
        *,
        table_name: str,
        data_path: str | Path,
        unique_key: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Merge staged parquet data into a destination table."""
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;data_path&#x22;" type="&#x22;str | Path&#x22;" value="null" />

    <PyParameter name="&#x22;unique_key&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, int]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;overwrite_parquet&#x22;" type="&#x22;(self, *, table_name, data_path, override_ref=None) -> dict[str, int]&#x22;">
  Overwrite a table with staged parquet data.

  <PySourceCode>
    ```python
    def overwrite_parquet(
        self,
        *,
        table_name: str,
        data_path: str | Path,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Overwrite a table with staged parquet data."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;data_path&#x22;" type="&#x22;str | Path&#x22;" value="null" />

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, int]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;delete_rows&#x22;" type="&#x22;(self, *, table_name, predicate, override_ref=None) -> dict[str, int]&#x22;">
  Delete rows matching a predicate expression.

  <PySourceCode>
    ```python
    def delete_rows(
        self,
        *,
        table_name: str,
        predicate: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Delete rows matching a predicate expression."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;predicate&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, int]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;compact&#x22;" type="&#x22;(self, *, table_name, override_ref=None) -> dict[str, Any]&#x22;">
  Compact small files in a table.

  <PySourceCode>
    ```python
    def compact(
        self,
        *,
        table_name: str,
        override_ref: str | None = None,
    ) -> dict[str, Any]:
        """Compact small files in a table."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;override_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_snapshots&#x22;" type="&#x22;(self, *, table_name, limit=10) -> list[dict[str, Any]]&#x22;">
  List recent table snapshots for time-travel queries.

  <PySourceCode>
    ```python
    def list_snapshots(
        self,
        *,
        table_name: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """List recent table snapshots for time-travel queries."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;10&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;list[dict[str, typing.Any]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;rollback_to_snapshot&#x22;" type="&#x22;(self, *, table_name, snapshot_id) -> dict[str, Any]&#x22;">
  Roll back a table to a previous snapshot.

  <PySourceCode>
    ```python
    def rollback_to_snapshot(
        self,
        *,
        table_name: str,
        snapshot_id: int | str,
    ) -> dict[str, Any]:
        """Roll back a table to a previous snapshot."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;snapshot_id&#x22;" type="&#x22;int | str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;vacuum&#x22;" type="&#x22;(self, *, table_name, retain_hours=168) -> dict[str, Any]&#x22;">
  Remove orphan files older than the retention period.

  <PySourceCode>
    ```python
    def vacuum(
        self,
        *,
        table_name: str,
        retain_hours: int = 168,
    ) -> dict[str, Any]:
        """Remove orphan files older than the retention period."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;retain_hours&#x22;" type="&#x22;int&#x22;" value="&#x22;168&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
</PyFunction>
