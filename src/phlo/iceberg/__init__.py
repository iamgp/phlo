# __init__.py - Iceberg module initialization, exposing key functions for table and catalog operations
# This module serves as the entry point for Iceberg functionality in the lakehouse platform

"""
Iceberg integration for Cascade.

This module provides integration with Apache Iceberg using PyIceberg and Nessie catalog.
"""

from phlo.iceberg.catalog import get_catalog
from phlo.iceberg.tables import ensure_table, append_to_table, merge_to_table

# Public API: Only these functions are exposed when importing the module
__all__ = ["get_catalog", "ensure_table", "append_to_table", "merge_to_table"]
