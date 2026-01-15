"""Backward compatibility shim - import from phlo.operations.ingestion instead."""

import warnings

from phlo.operations.ingestion import BaseIngester, IngestionResult

warnings.warn(
    "phlo.ingestion is deprecated; import from phlo.operations.ingestion instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["BaseIngester", "IngestionResult"]
