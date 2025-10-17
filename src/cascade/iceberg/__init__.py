"""
Iceberg integration for Cascade.

This module provides integration with Apache Iceberg using PyIceberg and Nessie catalog.
"""

from cascade.iceberg.catalog import get_catalog
from cascade.iceberg.tables import ensure_table, append_to_table

__all__ = ["get_catalog", "ensure_table", "append_to_table"]
