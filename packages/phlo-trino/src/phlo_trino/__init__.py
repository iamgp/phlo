"""Trino service plugin package."""

from phlo_trino.plugin import TrinoResourceProvider, TrinoServicePlugin
from phlo_trino.resource import TrinoResource

__all__ = ["TrinoResourceProvider", "TrinoServicePlugin", "TrinoResource"]
__version__ = "0.1.0"
