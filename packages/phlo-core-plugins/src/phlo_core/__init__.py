"""Core plugins for Phlo.

This package provides the foundational set of plugins bundled with Phlo,
including quality check plugins and source connector plugins. These plugins
are automatically available when Phlo is installed.

Quality Checks:
    - NullCheckPlugin: Validates column completeness by checking for null values.
    - UniquenessCheckPlugin: Validates primary key uniqueness.
    - FreshnessCheckPlugin: Validates data freshness based on timestamps.
    - SchemaCheckPlugin: Validates column presence and data types.

Source Connectors:
    - RestAPIPlugin: Generic REST API connector for fetching data.

Example:
    To use these plugins in your Phlo project::

        from phlo_core import NullCheckPlugin, RestAPIPlugin

        null_check = NullCheckPlugin()
        rest_source = RestAPIPlugin()

Attributes:
    __version__: The version string for the phlo-core-plugins package.

"""

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
__version__ = "0.2.3"
