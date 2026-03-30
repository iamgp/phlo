# executor (/docs/python-reference/core/phlo/migrations/executor)



Migration execution engine.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;MigrationExecutionError&#x22;" href="&#x22;/docs/python-reference/core/phlo/migrations/executor/MigrationExecutionError&#x22;" />

      <Card title="&#x22;MigrationExecutor&#x22;" href="&#x22;/docs/python-reference/core/phlo/migrations/executor/MigrationExecutor&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;read_migration_history&#x22;" type="&#x22;(limit=10) -> list[dict[str, Any]]&#x22;">
      Read recent migration results from local history.

      <PySourceCode>
        ```python
        def read_migration_history(limit: int = 10) -> list[dict[str, Any]]:
            """Read recent migration results from local history."""
            if limit <= 0:
                return []
            if not _HISTORY_PATH.exists():
                return []

            lines = _HISTORY_PATH.read_text(encoding="utf-8").splitlines()
            payloads: list[dict[str, Any]] = []
            for line in reversed(lines):
                if len(payloads) >= limit:
                    break
                try:
                    loaded = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(loaded, dict):
                    payloads.append(loaded)
            return payloads
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;10&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;list[dict[str, typing.Any]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_append_history&#x22;" type="&#x22;(result) -> None&#x22;">
      <PySourceCode>
        ```python
        def _append_history(result: MigrationResult) -> None:
            _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            with _HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(f"{json.dumps(asdict(result), sort_keys=False)}\n")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;result&#x22;" type="&#x22;MigrationResult&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_apply_column_mapping&#x22;" type="&#x22;(rows, column_mapping) -> list[dict[str, Any]]&#x22;">
      <PySourceCode>
        ```python
        def _apply_column_mapping(
            rows: list[dict[str, Any]],
            column_mapping: dict[str, str],
        ) -> list[dict[str, Any]]:
            if not column_mapping:
                return rows
            mapped_rows: list[dict[str, Any]] = []
            for row in rows:
                mapped: dict[str, Any] = {}
                for key, value in row.items():
                    mapped[column_mapping.get(key, key)] = value
                mapped_rows.append(mapped)
            return mapped_rows
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;rows&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="null" />

        <PyParameter name="&#x22;column_mapping&#x22;" type="&#x22;dict[str, str]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;list[dict[str, typing.Any]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_resolve_quality_schema&#x22;" type="&#x22;(reference) -> Any&#x22;">
      <PySourceCode>
        ```python
        def _resolve_quality_schema(reference: str) -> Any:
            if "::" not in reference:
                raise MigrationExecutionError(
                    "options.quality_schema must use '<path>.py::ClassName' format"
                )

            module_path, class_name = reference.split("::", 1)
            schema_path = Path(module_path)
            if not schema_path.exists():
                raise MigrationExecutionError(f"Quality schema path not found: {schema_path}")

            import importlib.util

            module_name = f"phlo_migration_quality_{abs(hash(schema_path.resolve()))}"
            spec = importlib.util.spec_from_file_location(module_name, schema_path)
            if spec is None or spec.loader is None:
                raise MigrationExecutionError(f"Could not load quality schema module: {schema_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            schema = getattr(module, class_name, None)
            if schema is None:
                raise MigrationExecutionError(
                    f"Quality schema class '{class_name}' not found in {schema_path}"
                )
            return schema
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;reference&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_validate_quality_chunk&#x22;" type="&#x22;(schema, rows) -> None&#x22;">
      <PySourceCode>
        ```python
        def _validate_quality_chunk(schema: Any, rows: list[dict[str, Any]]) -> None:
            if not hasattr(schema, "validate"):
                raise MigrationExecutionError(
                    "Configured quality schema does not expose a 'validate' method"
                )

            try:
                import pandas as pd
            except ImportError as exc:
                raise MigrationExecutionError(
                    "pandas is required for chunk-level quality validation"
                ) from exc

            frame = pd.DataFrame(rows)
            schema.validate(frame)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;schema&#x22;" type="&#x22;Any&#x22;" value="null" />

        <PyParameter name="&#x22;rows&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_write_chunk_to_table_store&#x22;" type="&#x22;(*, table_store, table_name, write_mode, unique_key, chunk, first_chunk) -> None&#x22;">
      <PySourceCode>
        ```python
        def _write_chunk_to_table_store(
            *,
            table_store: Any,
            table_name: str,
            write_mode: str,
            unique_key: str | None,
            chunk: list[dict[str, Any]],
            first_chunk: bool,
        ) -> None:
            parquet_path = _stage_chunk_parquet(chunk)
            try:
                if write_mode == "append":
                    table_store.append_parquet(table_name=table_name, data_path=parquet_path)
                    return
                if write_mode == "overwrite":
                    if not hasattr(table_store, "overwrite_parquet"):
                        raise MigrationExecutionError(
                            "write_mode 'overwrite' requires table store support for overwrite_parquet"
                        )
                    if first_chunk:
                        table_store.overwrite_parquet(table_name=table_name, data_path=parquet_path)
                    else:
                        table_store.append_parquet(table_name=table_name, data_path=parquet_path)
                    return
                if write_mode == "merge":
                    if not unique_key:
                        raise MigrationExecutionError("unique_key is required for merge mode")
                    table_store.merge_parquet(
                        table_name=table_name,
                        data_path=parquet_path,
                        unique_key=unique_key,
                    )
                    return
                raise MigrationExecutionError(f"Unsupported write_mode: {write_mode}")
            finally:
                parquet_path.unlink(missing_ok=True)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_store&#x22;" type="&#x22;Any&#x22;" value="null" />

        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;write_mode&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;unique_key&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;chunk&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="null" />

        <PyParameter name="&#x22;first_chunk&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_stage_chunk_parquet&#x22;" type="&#x22;(chunk) -> Path&#x22;">
      <PySourceCode>
        ```python
        def _stage_chunk_parquet(chunk: list[dict[str, Any]]) -> Path:
            try:
                import pyarrow as pa
                import pyarrow.parquet as pq
            except ImportError as exc:
                raise MigrationExecutionError(
                    "pyarrow is required for non-dry-run migration writes"
                ) from exc

            table = pa.Table.from_pylist(chunk)
            with tempfile.NamedTemporaryFile(
                prefix="phlo-migrate-", suffix=".parquet", delete=False
            ) as tmp:
                temp_path = Path(tmp.name)
            try:
                pq.write_table(table, temp_path)
            except Exception:
                temp_path.unlink(missing_ok=True)
                raise
            return temp_path
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;chunk&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
