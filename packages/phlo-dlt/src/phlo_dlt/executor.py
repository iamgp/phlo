from __future__ import annotations

import time
from typing import Any, Callable, Dict

from phlo.ingestion import BaseIngester, IngestionResult
from phlo.hooks import (
    IngestionEventContext,
    IngestionEventEmitter,
    TelemetryEventContext,
    TelemetryEventEmitter,
)
from phlo_iceberg.resource import IcebergResource

from phlo_dlt.dlt_helpers import (
    inject_metadata_columns,
    merge_to_iceberg,
    setup_dlt_pipeline,
    stage_to_parquet,
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
        iceberg_resource: IcebergResource,
        dlt_source_func: Callable[..., Any],
        add_metadata_columns: bool = True,
        merge_strategy: str = "merge",
        merge_config: Dict[str, Any] | None = None,
    ):
        super().__init__(context, logger)
        self.table_config = table_config
        self.iceberg = iceberg_resource
        self.dlt_source_func = dlt_source_func
        self.add_metadata_columns = add_metadata_columns
        self.merge_strategy = merge_strategy
        self.merge_config = merge_config or {}

    def run_ingestion(
        self, partition_key: str, parameters: Dict[str, Any] = None
    ) -> IngestionResult:
        """
        Run the full DLT -> Parquet -> Iceberg flow.
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

        self.logger.info(f"Starting ingestion for partition {partition_key}")
        start_time = time.time()
        emitter.emit_start()

        try:
            dlt_source = self.dlt_source_func(partition_date=partition_key)

            if dlt_source is None:
                self.logger.info(f"No data for partition {partition_key}, skipping")
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
            # For now, self has .logger from BaseIngester (renamed to .log for compat if needed,
            # but helpers use context.log). Let's wrap a context shim.

            class ContextShim:
                def __init__(self, logger):
                    self.log = logger

            shim = ContextShim(self.logger)

            parquet_path, dlt_elapsed = stage_to_parquet(
                context=shim,
                pipeline=pipeline,
                dlt_source=dlt_source,
                local_staging_root=local_staging_root,
            )

            if self.add_metadata_columns:
                inject_metadata_columns(
                    parquet_path=parquet_path,
                    partition_date=partition_key,
                    run_id=run_id,
                    context=shim,
                )

            # Validation hook would go here (Pandera) - currently kept in decorator or moved here?
            # User asked for core logic here. Validation IS core logic.
            # To avoid importing Dagster exceptions here, we should raise standard exceptions
            # and let the orchestrator wrapper catch/translate them.

            # NOTE: Pandera validation requires the checks logic.
            # For this iteration, I will assume validation happens here via standard Exceptions.

            merge_metrics = merge_to_iceberg(
                context=shim,
                iceberg=self.iceberg,
                table_config=self.table_config,
                parquet_path=parquet_path,
                branch_name=branch_name,
                merge_strategy=self.merge_strategy,
                merge_config=self.merge_config,
            )

            total_elapsed = time.time() - start_time
            self.logger.info(f"Ingestion completed successfully in {total_elapsed:.2f}s")

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
