# parser (/docs/python-reference/core/phlo/migrations/parser)



Migration spec parsing and validation.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;MigrationSpecError&#x22;" href="&#x22;/docs/python-reference/core/phlo/migrations/parser/MigrationSpecError&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;load_migration_spec&#x22;" type="&#x22;(path) -> MigrationSpec&#x22;">
      Load a migration spec from YAML.

      <PySourceCode>
        ```python
        def load_migration_spec(path: Path) -> MigrationSpec:
            """Load a migration spec from YAML."""
            if not path.exists():
                raise MigrationSpecError(f"Migration spec file not found: {path}")

            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise MigrationSpecError("Migration spec root must be a mapping")

            name = _require_str(raw, "name")
            version = str(raw.get("version", "1.0"))
            description = str(raw.get("description", ""))

            source_raw = _require_mapping(raw, "source")
            source = MigrationSource(
                type=_require_str(source_raw, "type"),
                connection=_optional_str(source_raw.get("connection")),
                query=_optional_str(source_raw.get("query")),
                table=_optional_str(source_raw.get("table")),
                path=_optional_str(source_raw.get("path")),
                options={
                    key: value
                    for key, value in source_raw.items()
                    if key not in {"type", "connection", "query", "table", "path"}
                },
            )

            destination_raw = _require_mapping(raw, "destination")
            destination = MigrationDestination(
                table=_require_str(destination_raw, "table"),
                write_mode=_optional_str(destination_raw.get("write_mode")) or "append",
                unique_key=_optional_str(destination_raw.get("unique_key")),
            )

            options_raw = _optional_mapping(raw, "options") or {}
            options = MigrationOptions(
                chunk_size=_optional_int(options_raw.get("chunk_size"), 50_000),
                parallelism=_optional_int(options_raw.get("parallelism"), 1),
                validate=_optional_bool(options_raw.get("validate"), True),
                dry_run=_optional_bool(options_raw.get("dry_run"), False),
                quality_schema=_optional_str(options_raw.get("quality_schema")),
            )

            column_mapping_raw = raw.get("column_mapping", {})
            if not isinstance(column_mapping_raw, dict):
                raise MigrationSpecError("column_mapping must be a mapping")
            column_mapping: dict[str, str] = {}
            for source_name, destination_name in column_mapping_raw.items():
                if not isinstance(source_name, str) or not isinstance(destination_name, str):
                    raise MigrationSpecError("column_mapping keys and values must be strings")
                column_mapping[source_name] = destination_name

            if options.chunk_size <= 0:
                raise MigrationSpecError("options.chunk_size must be > 0")
            if options.parallelism <= 0:
                raise MigrationSpecError("options.parallelism must be > 0")

            write_mode = destination.write_mode.lower()
            if write_mode not in {"append", "overwrite", "merge"}:
                raise MigrationSpecError("destination.write_mode must be one of: append, overwrite, merge")
            if write_mode == "merge" and not destination.unique_key:
                raise MigrationSpecError("destination.unique_key is required for merge write_mode")

            return MigrationSpec(
                name=name,
                version=version,
                description=description,
                source=source,
                destination=MigrationDestination(
                    table=destination.table,
                    write_mode=write_mode,
                    unique_key=destination.unique_key,
                ),
                options=options,
                column_mapping=column_mapping,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.migrations.specs.MigrationSpec&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_require_mapping&#x22;" type="&#x22;(payload, key) -> dict[str, Any]&#x22;">
      <PySourceCode>
        ```python
        def _require_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
            value = payload.get(key)
            if value is None:
                raise MigrationSpecError(f"Missing required field: {key}")
            if not isinstance(value, dict):
                raise MigrationSpecError(f"{key} must be a mapping")
            return value
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;payload&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />

        <PyParameter name="&#x22;key&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_optional_mapping&#x22;" type="&#x22;(payload, key) -> dict[str, Any] | None&#x22;">
      <PySourceCode>
        ```python
        def _optional_mapping(payload: dict[str, Any], key: str) -> dict[str, Any] | None:
            value = payload.get(key)
            if value is None:
                return None
            if not isinstance(value, dict):
                raise MigrationSpecError(f"{key} must be a mapping")
            return value
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;payload&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />

        <PyParameter name="&#x22;key&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any] | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_require_str&#x22;" type="&#x22;(payload, key) -> str&#x22;">
      <PySourceCode>
        ```python
        def _require_str(payload: dict[str, Any], key: str) -> str:
            value = payload.get(key)
            if not isinstance(value, str) or not value.strip():
                raise MigrationSpecError(f"{key} is required and must be a non-empty string")
            return value
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;payload&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />

        <PyParameter name="&#x22;key&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_optional_str&#x22;" type="&#x22;(value) -> str | None&#x22;">
      <PySourceCode>
        ```python
        def _optional_str(value: Any) -> str | None:
            if value is None:
                return None
            if not isinstance(value, str):
                raise MigrationSpecError(f"Expected string value, got {type(value).__name__}")
            return value
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_optional_int&#x22;" type="&#x22;(value, default) -> int&#x22;">
      <PySourceCode>
        ```python
        def _optional_int(value: Any, default: int) -> int:
            if value is None:
                return default
            if isinstance(value, bool) or not isinstance(value, int):
                raise MigrationSpecError(f"Expected integer value, got {type(value).__name__}")
            return value
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />

        <PyParameter name="&#x22;default&#x22;" type="&#x22;int&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;int&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_optional_bool&#x22;" type="&#x22;(value, default) -> bool&#x22;">
      <PySourceCode>
        ```python
        def _optional_bool(value: Any, default: bool) -> bool:
            if value is None:
                return default
            if not isinstance(value, bool):
                raise MigrationSpecError(f"Expected boolean value, got {type(value).__name__}")
            return value
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />

        <PyParameter name="&#x22;default&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
