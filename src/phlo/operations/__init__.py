"""Phlo operations: ingestion and transformation base classes."""

from phlo.operations.adapters import (
    AsyncToSyncIngesterAdapter,
    AsyncToSyncTransformerAdapter,
    SyncToAsyncIngesterAdapter,
    SyncToAsyncTransformerAdapter,
)
from phlo.operations.ingestion import AsyncIngester, BaseIngester, IngestionResult
from phlo.operations.transformation import AsyncTransformer, BaseTransformer, TransformationResult

__all__ = [
    "AsyncToSyncIngesterAdapter",
    "AsyncToSyncTransformerAdapter",
    "AsyncIngester",
    "AsyncTransformer",
    "BaseIngester",
    "BaseTransformer",
    "IngestionResult",
    "SyncToAsyncIngesterAdapter",
    "SyncToAsyncTransformerAdapter",
    "TransformationResult",
]
