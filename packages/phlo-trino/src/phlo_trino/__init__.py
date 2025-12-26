"""Trino service plugin package."""

from phlo_trino.plugin import TrinoServicePlugin
from phlo_trino.resource import TrinoResource

__all__ = ["TrinoServicePlugin", "TrinoResource"]
__version__ = "0.1.0"
