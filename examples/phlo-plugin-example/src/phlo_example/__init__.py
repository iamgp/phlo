"""
Example plugin package for Phlo.

Demonstrates how to create source, quality check, transform, and service plugins.
"""

from phlo_example.quality import ThresholdCheckPlugin
from phlo_example.service import ExampleCacheServicePlugin
from phlo_example.source import JSONPlaceholderSource
from phlo_example.transform import UppercaseTransformPlugin

__all__ = [
    "JSONPlaceholderSource",
    "ThresholdCheckPlugin",
    "ExampleCacheServicePlugin",
    "UppercaseTransformPlugin",
]
__version__ = "1.0.0"
