# DltIngester (/docs/python-reference/packages/phlo-dlt/phlo_dlt/executor/DltIngester)



DLT-specific implementation of the ingestion engine.

This class orchestrates the complete DLT-based ingestion flow, from
extracting data via DLT to loading it into the configured table store.
It implements the orchestrator-agnostic BaseIngester interface.

The ingester supports:

* DLT extraction to Parquet
* Automatic metadata column injection
* Pandera schema validation
* Strict validation with WAP pattern
* Append and merge strategies
* Telemetry and event emission

Attributes [#attributes]

<PyAttribute name="&#x22;table_config&#x22;" type="null" value="&#x22;table_config&#x22;">
  Table-level ingestion configuration.
</PyAttribute>

<PyAttribute name="&#x22;table_store&#x22;" type="null" value="&#x22;table_store_resource&#x22;">
  Table store capability for merge operations.
</PyAttribute>

<PyAttribute name="&#x22;dlt_source_func&#x22;" type="null" value="&#x22;dlt_source_func&#x22;">
  Callable that builds a DLT source for a partition.
</PyAttribute>

<PyAttribute name="&#x22;validation_schema&#x22;" type="null" value="&#x22;validation_schema&#x22;">
  Optional Pandera schema for validation.
</PyAttribute>

<PyAttribute name="&#x22;validate&#x22;" type="null" value="&#x22;validate&#x22;">
  Whether to run Pandera validation.
</PyAttribute>

<PyAttribute name="&#x22;strict_validation&#x22;" type="null" value="&#x22;strict_validation&#x22;">
  Whether to fail on validation errors.
</PyAttribute>

<PyAttribute name="&#x22;add_metadata_columns&#x22;" type="null" value="&#x22;add_metadata_columns&#x22;">
  Whether to inject metadata columns.
</PyAttribute>

<PyAttribute name="&#x22;merge_strategy&#x22;" type="null" value="&#x22;merge_strategy&#x22;">
  Merge strategy ("append" or "merge").
</PyAttribute>

<PyAttribute name="&#x22;merge_config&#x22;" type="null" value="&#x22;merge_config or {}&#x22;">
  Additional merge configuration options.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, context, logger, table_config, table_store_resource, dlt_source_func, validation_schema=None, validate=True, strict_validation=True, add_metadata_columns=True, merge_strategy='merge', merge_config=None)&#x22;">
  Initialize the DLT ingester.

  <PySourceCode>
    ```python
    def __init__(
        self,
        context: Any,  # Can be generic context or specific object with .log/.run_id
        logger: Any,
        table_config: TableConfig,
        table_store_resource: TableStore,
        dlt_source_func: Callable[..., Any],
        validation_schema: type[Any] | None = None,
        validate: bool = True,
        strict_validation: bool = True,
        add_metadata_columns: bool = True,
        merge_strategy: str = "merge",
        merge_config: Dict[str, Any] | None = None,
    ):
        """Initialize the DLT ingester.

        Args:
            context: Execution context from the orchestrator runtime.
                Should have log/run_id attributes or be compatible.
            logger: Logger used for ingestion lifecycle messages.
            table_config: Table-level ingestion configuration.
            table_store_resource: Table store resource used for merge operations.
            dlt_source_func: Callable that builds a DLT source for a partition.
                Signature: (partition_date: str) -> DltSource
            validation_schema: Optional Pandera schema used for staged-data validation.
            validate: Whether Pandera validation should run for staged data.
            strict_validation: Whether failed validation should abort before visible writes.
                When True, enables WAP pattern with isolated branches.
            add_metadata_columns: Whether to inject metadata columns into staged parquet.
            merge_strategy: Merge strategy name for table-store writes.
                Options: "append" (insert only), "merge" (upsert on unique_key).
            merge_config: Optional merge strategy configuration dictionary.

        """
        super().__init__(context, logger)
        self.table_config = table_config
        self.table_store = table_store_resource
        self.dlt_source_func = dlt_source_func
        self.validation_schema = validation_schema
        self.validate = validate
        self.strict_validation = strict_validation
        self.add_metadata_columns = add_metadata_columns
        self.merge_strategy = merge_strategy
        self.merge_config = merge_config or {}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Execution context from the orchestrator runtime.
      Should have log/run\_id attributes or be compatible.
    </PyParameter>

    <PyParameter name="&#x22;logger&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Logger used for ingestion lifecycle messages.
    </PyParameter>

    <PyParameter name="&#x22;table_config&#x22;" type="&#x22;TableConfig&#x22;" value="undefined">
      Table-level ingestion configuration.
    </PyParameter>

    <PyParameter name="&#x22;table_store_resource&#x22;" type="&#x22;TableStore&#x22;" value="undefined">
      Table store resource used for merge operations.
    </PyParameter>

    <PyParameter name="&#x22;dlt_source_func&#x22;" type="&#x22;Callable[..., Any]&#x22;" value="undefined">
      Callable that builds a DLT source for a partition.
      Signature: (partition\_date: str) -> DltSource
    </PyParameter>

    <PyParameter name="&#x22;validation_schema&#x22;" type="&#x22;type[Any] | None&#x22;" value="&#x22;None&#x22;">
      Optional Pandera schema used for staged-data validation.
    </PyParameter>

    <PyParameter name="&#x22;validate&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      Whether Pandera validation should run for staged data.
    </PyParameter>

    <PyParameter name="&#x22;strict_validation&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      Whether failed validation should abort before visible writes.
      When True, enables WAP pattern with isolated branches.
    </PyParameter>

    <PyParameter name="&#x22;add_metadata_columns&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      Whether to inject metadata columns into staged parquet.
    </PyParameter>

    <PyParameter name="&#x22;merge_strategy&#x22;" type="&#x22;str&#x22;" value="&#x22;'merge'&#x22;">
      Merge strategy name for table-store writes.
      Options: "append" (insert only), "merge" (upsert on unique\_key).
    </PyParameter>

    <PyParameter name="&#x22;merge_config&#x22;" type="&#x22;Dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Optional merge strategy configuration dictionary.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;run_ingestion&#x22;" type="&#x22;(self, partition_key, parameters=None) -> IngestionResult&#x22;">
  Run the full DLT -> Parquet -> table\_store flow.

  Executes the complete ingestion pipeline:

  1. Calls dlt\_source\_func to get DLT source
  2. If no data, returns no\_data result
  3. Stages data to Parquet via DLT
  4. Injects metadata columns (if enabled)
  5. Runs Pandera validation (if enabled)
  6. Merges to table store
  7. Emits events and returns result

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    result = ingester.run_ingestion(
        partition_key="2024-01-01",
        parameters=\{
            "branch_name": "main",
            "target_branch_name": "main",
            "run_id": "dagster-run-123",
        \}
    )
    print(f"Status: \{result.status\}, Rows: \{result.rows_inserted\}")
    ```
  </Callout>

  <PySourceCode>
    ````python
    def run_ingestion(
        self, partition_key: str, parameters: Dict[str, Any] | None = None
    ) -> IngestionResult:
        """Run the full DLT -> Parquet -> table_store flow.

        Executes the complete ingestion pipeline:
        1. Calls dlt_source_func to get DLT source
        2. If no data, returns no_data result
        3. Stages data to Parquet via DLT
        4. Injects metadata columns (if enabled)
        5. Runs Pandera validation (if enabled)
        6. Merges to table store
        7. Emits events and returns result

        Args:
            partition_key: The partition date (YYYY-MM-DD) to ingest.
            parameters: Optional dict with:
                - branch_name: Target branch for writing
                - target_branch_name: Final target branch (for WAP)
                - run_id: Orchestrator run identifier

        Returns:
            IngestionResult: Result with status, row counts, and metadata.

        Raises:
            PanderaContractValidationError: If strict validation fails.
            RuntimeError: If any other error occurs during ingestion.

        Example:
            \```python
            result = ingester.run_ingestion(
                partition_key="2024-01-01",
                parameters={
                    "branch_name": "main",
                    "target_branch_name": "main",
                    "run_id": "dagster-run-123",
                }
            )
            print(f"Status: {result.status}, Rows: {result.rows_inserted}")
            \```

        """
        parameters = parameters or {}
        branch_name = parameters.get("branch_name", "main")
        target_branch_name = parameters.get("target_branch_name", branch_name)
        run_id = parameters.get("run_id", "unknown")

        pipeline_name = f"{self.table_config.table_name}_{partition_key.replace('-', '_')}"
        group_name = self.table_config.group_name

        # Emission Setup
        emitter = IngestionEventEmitter(
            IngestionEventContext(
                asset_key=f"dlt_{self.table_config.table_name}",
                table_name=self.table_config.full_table_name,
                group_name=group_name,
                partition_key=partition_key,
                run_id=run_id,
                branch_name=branch_name,
                tags={"group": group_name, "source": "dlt"},
                correlation=HookCorrelation(
                    run_id=run_id,
                    asset_key=f"dlt_{self.table_config.table_name}",
                    partition_key=partition_key,
                    job_name=getattr(self.context, "job_name", None),
                ),
            )
        )
        telemetry = TelemetryEventEmitter(
            TelemetryEventContext(
                tags={
                    "asset": f"dlt_{self.table_config.table_name}",
                    "group": group_name,
                    "source": "dlt",
                },
                correlation=HookCorrelation(
                    run_id=run_id,
                    asset_key=f"dlt_{self.table_config.table_name}",
                    partition_key=partition_key,
                    job_name=getattr(self.context, "job_name", None),
                ),
            )
        )

        log_event(self.logger, "info", "starting_ingestion", partition_key=partition_key)
        start_time = time.time()
        emitter.emit_start()

        try:
            dlt_source = self.dlt_source_func(partition_date=partition_key)

            if dlt_source is None:
                log_event(self.logger, "info", "ingestion_no_data", partition_key=partition_key)
                emitter.emit_end(status="no_data", metrics={"rows_loaded": 0})
                return IngestionResult(
                    status="no_data",
                    rows_inserted=0,
                    rows_deleted=0,
                    metadata={"status": "no_data"},
                )

            pipeline, local_staging_root = setup_dlt_pipeline(
                pipeline_name=pipeline_name,
                dataset_name=group_name,
            )

            # We pass 'self' as context because dlt_helpers expects an object with .log
            # In a real refactor, dlt_helpers should take logger explicitly.
            # Helpers consume context.log, so wrap logger behind a tiny shim.

            class ContextShim:
                """Expose a `.log` attribute expected by DLT helpers."""

                def __init__(self, logger):
                    """Store logger on `.log` to match helper context contract.

                    Args:
                        logger: Logger instance consumed by helper functions.

                    """
                    self.log = logger

            shim = ContextShim(self.logger)

            parquet_paths, dlt_elapsed = stage_to_parquet(
                context=shim,
                pipeline=pipeline,
                dlt_source=dlt_source,
                local_staging_root=local_staging_root,
            )

            if self.add_metadata_columns:
                for parquet_path in parquet_paths:
                    inject_metadata_columns(
                        parquet_path=parquet_path,
                        partition_date=partition_key,
                        run_id=run_id,
                        context=shim,
                    )

            evaluation_metadata: dict[str, Any] | None = None
            if self.validate and self.validation_schema is not None:
                evaluation = evaluate_pandera_contract_parquet_files(
                    parquet_paths,
                    schema_class=self.validation_schema,
                )
                evaluation_metadata = serialize_pandera_contract_evaluation(evaluation)
                if self.strict_validation and not evaluation.passed:
                    raise PanderaContractValidationError(
                        evaluation=evaluation,
                        parquet_paths=tuple(parquet_paths),
                    )

            merge_metrics = merge_to_table_store(
                context=shim,
                table_store=self.table_store,
                table_config=self.table_config,
                parquet_paths=parquet_paths,
                branch_name=branch_name,
                merge_strategy=self.merge_strategy,
                merge_config=self.merge_config,
            )

            total_elapsed = time.time() - start_time
            log_event(
                self.logger,
                "info",
                "ingestion_completed",
                partition_key=partition_key,
                total_elapsed_seconds=total_elapsed,
            )

            emitter.emit_end(
                status="success",
                metrics={
                    "rows_inserted": merge_metrics["rows_inserted"],
                    "rows_deleted": merge_metrics.get("rows_deleted", 0),
                    "dlt_elapsed_seconds": dlt_elapsed,
                    "total_elapsed_seconds": total_elapsed,
                    "target_branch_name": target_branch_name,
                },
            )

            return IngestionResult(
                status="success",
                rows_inserted=merge_metrics["rows_inserted"],
                rows_deleted=merge_metrics.get("rows_deleted", 0),
                metadata={
                    "dlt_elapsed_seconds": dlt_elapsed,
                    "parquet_path": str(parquet_paths[0]),
                    "parquet_paths": [str(parquet_path) for parquet_path in parquet_paths],
                    "pandera_evaluation": evaluation_metadata,
                    "total_elapsed_seconds": total_elapsed,
                    "target_branch_name": target_branch_name,
                },
            )

        except Exception as exc:
            total_elapsed = time.time() - start_time
            emitter.emit_end(
                status="failure",
                metrics={"total_elapsed_seconds": total_elapsed},
                error=str(exc),
            )
            telemetry.emit_log(
                name="ingestion.failure",
                level="error",
                payload={"error": str(exc), "elapsed_seconds": total_elapsed},
            )
            # Re-raise so the orchestrator knows it failed
            raise
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str&#x22;" value="undefined">
      The partition date (YYYY-MM-DD) to ingest.
    </PyParameter>

    <PyParameter name="&#x22;parameters&#x22;" type="&#x22;Dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Optional dict with:

      * branch\_name: Target branch for writing
      * target\_branch\_name: Final target branch (for WAP)
      * run\_id: Orchestrator run identifier
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo.operations.ingestion.IngestionResult&#x22;">
    Result with status, row counts, and metadata.
  </PyFunctionReturn>
</PyFunction>
