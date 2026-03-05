from __future__ import annotations

import time
from typing import Any, Callable, Dict

from phlo.logging import log_event
from phlo.operations.ingestion import BaseIngester, IngestionResult
from phlo.hooks import (
    IngestionEventContext,
    IngestionEventEmitter,
    TelemetryEventContext,
    TelemetryEventEmitter,
)
from phlo.capabilities.interfaces import TableStore

from phlo_dlt.dlt_helpers import (
    inject_metadata_columns,
    merge_to_table_store,
    setup_dlt_pipeline,
    stage_to_parquet,
)
from phlo_dlt.pandera_checks import (
    PanderaContractValidationError,
    evaluate_pandera_contract_parquet_files,
    serialize_pandera_contract_evaluation,
)
from phlo_dlt.registry import TableConfig


class DltIngester(BaseIngester):
    """
    DLT-specific implementation of the ingestion engine.
    Orchestrator-agnostic.
    """

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
            logger: Logger used for ingestion lifecycle messages.
            table_config: Table-level ingestion configuration.
            table_store_resource: Table store resource used for merge operations.
            dlt_source_func: Callable that builds a DLT source for a partition.
            validation_schema: Optional Pandera schema used for staged-data validation.
            validate: Whether Pandera validation should run for staged data.
            strict_validation: Whether failed validation should abort before visible writes.
            add_metadata_columns: Whether to inject metadata columns into staged parquet.
            merge_strategy: Merge strategy name for table-store writes.
            merge_config: Optional merge strategy configuration.
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

    def run_ingestion(
        self, partition_key: str, parameters: Dict[str, Any] | None = None
    ) -> IngestionResult:
        """
        Run the full DLT -> Parquet -> table_store flow.
        """
        parameters = parameters or {}
        branch_name = parameters.get("branch_name", "main")
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
            )
        )
        telemetry = TelemetryEventEmitter(
            TelemetryEventContext(
                tags={
                    "asset": f"dlt_{self.table_config.table_name}",
                    "group": group_name,
                    "source": "dlt",
                }
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
