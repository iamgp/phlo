"""Phlo core glue package."""

from __future__ import annotations

from phlo_dlt.decorator import phlo_ingestion as ingestion
from phlo_quality.decorator import phlo_quality as quality

__version__ = "0.1.0-alpha.1"
__all__ = ["__version__", "ingestion", "quality"]
