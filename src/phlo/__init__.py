"""Phlo core glue package."""

from __future__ import annotations

from importlib.metadata import version

from phlo_dlt.decorator import phlo_ingestion as ingestion
from phlo_quality.decorator import phlo_quality as quality

__version__ = version("phlo")
__all__ = ["__version__", "ingestion", "quality"]
