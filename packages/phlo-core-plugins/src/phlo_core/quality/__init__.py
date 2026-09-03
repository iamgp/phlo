"""Quality check plugins bundled with Phlo.

This module provides a collection of quality check plugins that can be used
to validate data integrity, completeness, freshness, and schema conformance.
These plugins integrate with the Phlo quality framework and can be applied to
Pandera schemas or used directly in data pipelines.

Available Plugins:
    - NullCheckPlugin: Checks for null values in specified columns with
        configurable thresholds.
    - UniquenessCheckPlugin: Validates that specified columns contain unique
        values, with optional tolerance for duplicates.
    - FreshnessCheckPlugin: Validates that timestamped data is within an
        acceptable age range.
    - SchemaCheckPlugin: Validates that data conforms to an expected schema
        with correct columns and types.

Each plugin follows the QualityCheckPlugin interface and provides a
``create_check()`` method to instantiate the actual check object.

Example:
    Import and use quality plugins::

        from phlo_core.quality import NullCheckPlugin, FreshnessCheckPlugin

        # Create a null check for required columns
        null_plugin = NullCheckPlugin()
        null_check = null_plugin.create_check(
            columns=["id", "name", "email"],
            allow_threshold=0.01  # Allow up to 1% nulls
        )

        # Create a freshness check for data age
        freshness_plugin = FreshnessCheckPlugin()
        freshness_check = freshness_plugin.create_check(
            timestamp_column="created_at",
            max_age_hours=24
        )

"""

from phlo_core.quality.freshness_check import FreshnessCheckPlugin
from phlo_core.quality.null_check import NullCheckPlugin
from phlo_core.quality.schema_check import SchemaCheckPlugin
from phlo_core.quality.uniqueness_check import UniquenessCheckPlugin

__all__ = [
    "NullCheckPlugin",
    "UniquenessCheckPlugin",
    "FreshnessCheckPlugin",
    "SchemaCheckPlugin",
]
