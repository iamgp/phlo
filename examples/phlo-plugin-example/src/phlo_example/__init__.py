"""
Example plugin package for Cascade.

Demonstrates how to create source, quality check, and transform plugins.
"""

from phlo_example.quality import ThresholdCheckPlugin
from phlo_example.source import JSONPlaceholderSource
from phlo_example.transform import UppercaseTransformPlugin

__all__ = [
    "JSONPlaceholderSource",
    "ThresholdCheckPlugin",
    "UppercaseTransformPlugin",
]
__version__ = "1.0.0"
