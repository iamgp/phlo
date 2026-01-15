"""Backward compatibility shim - import from phlo.operations.ingestion instead."""

from phlo.operations.ingestion import BaseIngester, IngestionResult

__all__ = ["BaseIngester", "IngestionResult"]
