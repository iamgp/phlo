"""Phlo core glue package."""

from __future__ import annotations

from importlib.metadata import version

__version__ = version("phlo")
__all__ = ["__version__"]

# Optional decorator imports - only available if packages are installed
try:
    from phlo_dlt.decorator import phlo_ingestion as ingestion

    __all__.append("ingestion")
except ImportError:
    pass

try:
    from phlo_quality.decorator import phlo_quality as quality

    __all__.append("quality")
except ImportError:
    pass
