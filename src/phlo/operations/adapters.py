"""Compatibility adapters for sync and async operation contracts."""

from __future__ import annotations

import asyncio
from typing import Any

from phlo.operations.ingestion import AsyncIngester, BaseIngester, IngestionResult
from phlo.operations.transformation import AsyncTransformer, BaseTransformer, TransformationResult


def _ensure_no_running_event_loop() -> None:
    """Raise a clear error when sync wrappers are used from an active event loop."""

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return
    raise RuntimeError(
        "Cannot run async operation from sync adapter while an event loop is running. "
        "Use the async operation directly."
    )


class SyncToAsyncIngesterAdapter(AsyncIngester):
    """Expose a sync ingester behind the async ingestion contract."""

    def __init__(self, ingester: BaseIngester):
        super().__init__(context=ingester.context, logger=ingester.logger)
        self._ingester = ingester

    async def run_ingestion(
        self,
        partition_key: str | None,
        parameters: dict[str, Any],
    ) -> IngestionResult:
        return await asyncio.to_thread(self._ingester.run_ingestion, partition_key, parameters)


class AsyncToSyncIngesterAdapter(BaseIngester):
    """Expose an async ingester behind the sync ingestion contract."""

    def __init__(self, ingester: AsyncIngester):
        super().__init__(context=ingester.context, logger=ingester.logger)
        self._ingester = ingester

    def run_ingestion(
        self,
        partition_key: str | None,
        parameters: dict[str, Any],
    ) -> IngestionResult:
        _ensure_no_running_event_loop()
        return asyncio.run(self._ingester.run_ingestion(partition_key, parameters))


class SyncToAsyncTransformerAdapter(AsyncTransformer[Any]):
    """Expose a sync transformer behind the async transform contract."""

    def __init__(self, transformer: BaseTransformer[Any]):
        super().__init__(context=transformer.context, logger=transformer.logger)
        self._transformer = transformer

    async def run_transform(
        self,
        partition_key: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> TransformationResult:
        return await asyncio.to_thread(self._transformer.run_transform, partition_key, parameters)


class AsyncToSyncTransformerAdapter(BaseTransformer[Any]):
    """Expose an async transformer behind the sync transform contract."""

    def __init__(self, transformer: AsyncTransformer[Any]):
        super().__init__(context=transformer.context, logger=transformer.logger)
        self._transformer = transformer

    def run_transform(
        self,
        partition_key: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> TransformationResult:
        _ensure_no_running_event_loop()
        return asyncio.run(self._transformer.run_transform(partition_key, parameters))
