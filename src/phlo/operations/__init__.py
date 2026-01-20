"""Phlo operations: ingestion and transformation base classes."""

from phlo.operations.ingestion import BaseIngester, IngestionResult
from phlo.operations.transformation import BaseTransformer, TransformationResult

__all__ = [
    "BaseIngester",
    "BaseTransformer",
    "IngestionResult",
    "TransformationResult",
]
