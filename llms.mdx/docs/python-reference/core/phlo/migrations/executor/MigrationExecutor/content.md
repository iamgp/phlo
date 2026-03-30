# MigrationExecutor (/docs/python-reference/core/phlo/migrations/executor/MigrationExecutor)



Execute data migrations from parsed specs.

Functions [#functions]

<PyFunction name="&#x22;validate&#x22;" type="&#x22;(self, spec, *, dry_run_override=None) -> list[str]&#x22;">
  Validate migration spec and environment without writing.

  <PySourceCode>
    ```python
    def validate(
        self,
        spec: MigrationSpec,
        *,
        dry_run_override: bool | None = None,
    ) -> list[str]:
        """Validate migration spec and environment without writing."""
        errors: list[str] = []
        dry_run = spec.options.dry_run if dry_run_override is None else dry_run_override
        discover_capabilities()

        adapter = resolve_source_adapter(spec.source.type)
        if adapter is None:
            supported = ", ".join(list_source_adapter_types()) or "none"
            errors.append(
                f"Unsupported source.type '{spec.source.type}'. Supported adapters: {supported}"
            )
            return errors

        errors.extend(adapter.validate_config(spec.source))

        if spec.destination.write_mode == "merge" and not spec.destination.unique_key:
            errors.append("destination.unique_key is required for merge write_mode")

        if not dry_run:
            resolution = resolve_capability("table_store")
            if resolution is None:
                configured_name = configured_capability_name("table_store")
                available = list_capabilities("table_store")
                if configured_name:
                    errors.append(
                        f"Configured table_store '{configured_name}' is not registered. "
                        f"Available providers: {available}"
                    )
                elif available:
                    errors.append(
                        "Multiple table_store providers are registered. "
                        f"Configure a default table_store provider: {available}"
                    )
                else:
                    errors.append(
                        "No table store registered. Install a table-store provider or run with --dry-run"
                    )

        if spec.options.quality_schema:
            try:
                _resolve_quality_schema(spec.options.quality_schema)
            except MigrationExecutionError as exc:
                errors.append(str(exc))

        return errors
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;MigrationSpec&#x22;" value="null" />

    <PyParameter name="&#x22;dry_run_override&#x22;" type="&#x22;bool | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, spec, *, dry_run_override=None) -> MigrationResult&#x22;">
  Execute a migration specification.

  <PySourceCode>
    ```python
    def execute(
        self, spec: MigrationSpec, *, dry_run_override: bool | None = None
    ) -> MigrationResult:
        """Execute a migration specification."""
        dry_run = spec.options.dry_run if dry_run_override is None else dry_run_override

        validation_errors = self.validate(spec, dry_run_override=dry_run_override)
        if validation_errors:
            raise MigrationExecutionError("; ".join(validation_errors))

        adapter = resolve_source_adapter(spec.source.type)
        if adapter is None:
            raise MigrationExecutionError(
                f"No adapter available for source type: {spec.source.type}"
            )

        table_store = None
        if not dry_run:
            resolution = resolve_capability("table_store")
            if resolution is None:
                configured_name = configured_capability_name("table_store")
                available = list_capabilities("table_store")
                if configured_name:
                    raise MigrationExecutionError(
                        f"Configured table_store '{configured_name}' is not registered. "
                        f"Available providers: {available}"
                    )
                if available:
                    raise MigrationExecutionError(
                        "Multiple table_store providers are registered. "
                        f"Configure PHLO_DEFAULT_CAPABILITIES to select one: {available}"
                    )
                raise MigrationExecutionError(
                    "No table store registered. Install a table-store provider or run with --dry-run"
                )
            table_store = resolution.provider

        request_id = uuid4().hex
        emitter = DataMigrationEventEmitter(
            DataMigrationEventContext(
                migration_name=spec.name,
                source_type=spec.source.type,
                destination_table=spec.destination.table,
                correlation=HookCorrelation(
                    request_id=request_id,
                    asset_key=spec.destination.table,
                ),
            )
        )

        rows_read = 0
        rows_written = 0
        rows_rejected = 0
        chunks_processed = 0
        validation_passed: bool | None = None
        started_at = time.perf_counter()

        estimated_rows = adapter.estimate_row_count(spec.source)
        emitter.emit(
            status="started",
            rows_read=0,
            rows_written=0,
            chunk_index=None,
            metrics={"estimated_rows": estimated_rows, "dry_run": dry_run},
        )

        quality_schema = None
        if spec.options.validate and spec.options.quality_schema:
            quality_schema = _resolve_quality_schema(spec.options.quality_schema)

        try:
            for index, chunk in enumerate(
                adapter.read_chunks(spec.source, chunk_size=spec.options.chunk_size), start=1
            ):
                mapped = _apply_column_mapping(chunk, spec.column_mapping)
                rows_read += len(mapped)

                if quality_schema is not None:
                    _validate_quality_chunk(quality_schema, mapped)

                if not dry_run and table_store is not None:
                    _write_chunk_to_table_store(
                        table_store=table_store,
                        table_name=spec.destination.table,
                        write_mode=spec.destination.write_mode,
                        unique_key=spec.destination.unique_key,
                        chunk=mapped,
                        first_chunk=index == 1,
                    )
                    rows_written += len(mapped)

                chunks_processed += 1
                emitter.emit(
                    status="chunk_complete",
                    rows_read=rows_read,
                    rows_written=rows_written,
                    chunk_index=index,
                    metrics={"chunk_rows": len(mapped)},
                )

            if quality_schema is not None:
                validation_passed = True
                emitter.emit(
                    status="validation",
                    rows_read=rows_read,
                    rows_written=rows_written,
                    chunk_index=None,
                    metrics={"validation_passed": True},
                )

            duration_seconds = time.perf_counter() - started_at
            status = "dry_run" if dry_run else "completed"
            result = MigrationResult(
                name=spec.name,
                status=status,
                rows_read=rows_read,
                rows_written=rows_written,
                rows_rejected=rows_rejected,
                chunks_processed=chunks_processed,
                duration_seconds=duration_seconds,
                validation_passed=validation_passed,
                metadata={
                    "destination_table": spec.destination.table,
                    "source_type": spec.source.type,
                    "write_mode": spec.destination.write_mode,
                    "dry_run": dry_run,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            emitter.emit(
                status="completed",
                rows_read=rows_read,
                rows_written=rows_written,
                chunk_index=None,
                metrics={"duration_seconds": duration_seconds},
            )
            _append_history(result)
            return result
        except Exception as exc:
            duration_seconds = time.perf_counter() - started_at
            emitter.emit(
                status="failed",
                rows_read=rows_read,
                rows_written=rows_written,
                chunk_index=None,
                metrics={"duration_seconds": duration_seconds, "error": str(exc)},
            )
            logger.exception(
                "migration_execution_failed",
                migration_name=spec.name,
                source_type=spec.source.type,
                destination_table=spec.destination.table,
            )
            raise
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;MigrationSpec&#x22;" value="null" />

    <PyParameter name="&#x22;dry_run_override&#x22;" type="&#x22;bool | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.migrations.specs.MigrationResult&#x22;" />
</PyFunction>
