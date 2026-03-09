"""Sling replication executor with hook event emission."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict

from phlo.logging import log_event
from phlo.operations.ingestion import BaseIngester, IngestionResult
from phlo.hooks import (
    HookCorrelation,
    IngestionEventContext,
    IngestionEventEmitter,
    TelemetryEventContext,
    TelemetryEventEmitter,
)

from phlo_sling.registry import ReplicationConfig


class SlingIngester(BaseIngester):
    """Sling-specific implementation of the ingestion engine.

    Mirrors DltIngester: wraps Sling execution with hook event emission,
    timing, and standardised IngestionResult output.
    """

    def __init__(
        self,
        context: Any,
        logger: Any,
        replication_config: ReplicationConfig,
        source_func: Callable[..., Any],
        overrides: dict[str, Any] | None = None,
    ):
        """Initialize the Sling ingester.

        Args:
            context: Execution context from the orchestrator runtime.
            logger: Logger used for replication lifecycle messages.
            replication_config: Replication-level configuration.
            source_func: The decorated user function (for reference).
            overrides: Optional runtime overrides returned by the user function.
        """
        super().__init__(context, logger)
        self.replication_config = replication_config
        self.source_func = source_func
        self.overrides = overrides or {}

    def run_ingestion(
        self, partition_key: str, parameters: Dict[str, Any] | None = None
    ) -> IngestionResult:
        """Run the Sling replication flow.

        Args:
            partition_key: Partition date string.
            parameters: Additional runtime parameters (run_id, etc.).

        Returns:
            IngestionResult with status, row counts, and metadata.
        """
        parameters = parameters or {}
        run_id = parameters.get("run_id", "unknown")
        config = self.replication_config

        emitter = IngestionEventEmitter(
            IngestionEventContext(
                asset_key=config.asset_key,
                table_name=config.full_table_name,
                group_name=config.group_name,
                partition_key=partition_key,
                run_id=run_id,
                tags={"group": config.group_name, "source": "sling", "mode": config.mode},
                correlation=HookCorrelation(
                    run_id=run_id,
                    asset_key=config.asset_key,
                    partition_key=partition_key,
                    job_name=getattr(self.context, "job_name", None),
                ),
            )
        )
        telemetry = TelemetryEventEmitter(
            TelemetryEventContext(
                tags={
                    "asset": config.asset_key,
                    "group": config.group_name,
                    "source": "sling",
                    "mode": config.mode,
                },
                correlation=HookCorrelation(
                    run_id=run_id,
                    asset_key=config.asset_key,
                    partition_key=partition_key,
                    job_name=getattr(self.context, "job_name", None),
                ),
            )
        )

        log_event(self.logger, "info", "starting_sling_replication", partition_key=partition_key)
        start_time = time.time()
        emitter.emit_start()

        try:
            from sling import Sling

            sling_kwargs = self._build_sling_kwargs(partition_key)
            sling_config = Sling(**sling_kwargs)

            log_event(
                self.logger,
                "info",
                "sling_execution_started",
                stream_name=config.stream_name,
                mode=config.mode,
            )

            sling_start = time.time()
            sling_config.run()
            sling_elapsed = time.time() - sling_start

            rows_inserted = getattr(sling_config, "rows_count", 0) or 0

            total_elapsed = time.time() - start_time
            log_event(
                self.logger,
                "info",
                "sling_replication_completed",
                partition_key=partition_key,
                rows_inserted=rows_inserted,
                sling_elapsed_seconds=sling_elapsed,
                total_elapsed_seconds=total_elapsed,
            )

            emitter.emit_end(
                status="success",
                metrics={
                    "rows_inserted": rows_inserted,
                    "sling_elapsed_seconds": sling_elapsed,
                    "total_elapsed_seconds": total_elapsed,
                },
            )

            return IngestionResult(
                status="success",
                rows_inserted=rows_inserted,
                rows_deleted=0,
                metadata={
                    "sling_elapsed_seconds": sling_elapsed,
                    "total_elapsed_seconds": total_elapsed,
                    "stream_name": config.stream_name,
                    "mode": config.mode,
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
                name="sling.replication.failure",
                level="error",
                payload={"error": str(exc), "elapsed_seconds": total_elapsed},
            )
            raise

    def _build_sling_kwargs(self, partition_key: str) -> dict[str, Any]:
        """Build keyword arguments for the Sling constructor.

        Merges static configuration from the ReplicationConfig with runtime
        overrides from the user function.

        Args:
            partition_key: Partition date for dynamic WHERE clause injection.

        Returns:
            Dict of kwargs suitable for `Sling(**kwargs)`.
        """
        config = self.replication_config

        kwargs: dict[str, Any] = {
            "src_conn": config.source_conn,
            "src_stream": config.stream_name,
            "mode": config.mode,
        }

        if config.target_conn:
            kwargs["tgt_conn"] = config.target_conn
        if config.object:
            kwargs["tgt_object"] = config.object
        if config.primary_key:
            kwargs["primary_key"] = config.primary_key
        if config.update_key:
            kwargs["update_key"] = config.update_key
        if config.select:
            kwargs["select"] = config.select
        if config.where:
            kwargs["where"] = config.where
        if config.source_options:
            kwargs["src_options"] = config.source_options
        if config.target_options:
            kwargs["tgt_options"] = config.target_options

        kwargs.update(self.overrides)

        return kwargs
