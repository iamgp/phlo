"""Core plugins for Phlo."""

from phlo_core.quality.freshness_check import FreshnessCheckPlugin
from phlo_core.quality.null_check import NullCheckPlugin
from phlo_core.quality.schema_check import SchemaCheckPlugin
from phlo_core.quality.uniqueness_check import UniquenessCheckPlugin
from phlo_core.sources.rest_api import RestAPIPlugin

__all__ = [
    "NullCheckPlugin",
    "UniquenessCheckPlugin",
    "FreshnessCheckPlugin",
    "SchemaCheckPlugin",
    "RestAPIPlugin",
]
__version__ = "0.1.0"
