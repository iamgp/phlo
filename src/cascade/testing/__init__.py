"""
Cascade Testing Utilities

This module provides testing utilities for Cascade workflows.

⚠️ **Note**: This module is under active development. Some features are placeholders
and will be fully implemented in future releases.

Available utilities:
- Mock DLT sources (planned)
- Mock Iceberg catalog (planned)
- Test asset execution (planned)
- Test fixtures (planned)

For current testing approaches, see: docs/TESTING_GUIDE.md
"""

from cascade.testing.placeholders import (
    mock_dlt_source,
    mock_iceberg_catalog,
    test_asset_execution,
    MockDLTSource,
    MockIcebergCatalog,
)

__all__ = [
    "mock_dlt_source",
    "mock_iceberg_catalog",
    "test_asset_execution",
    "MockDLTSource",
    "MockIcebergCatalog",
]

__version__ = "0.1.0-alpha"
