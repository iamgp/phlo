"""
Cascade Testing Utilities

This module provides testing utilities for Cascade workflows.

## Implemented (✅)
- MockDLTSource: Mock DLT sources for testing without API calls
- mock_dlt_source: Context manager for mocking DLT sources
- load_fixture: Load test fixtures from JSON/CSV/Parquet
- save_fixture: Save test data as fixtures

## Planned (⚠️)
- MockIcebergCatalog: Mock Iceberg catalog with DuckDB (~20h)
- test_asset_execution: Test assets without Docker (~30h)

For complete testing guide, see: docs/TESTING_GUIDE.md

## Quick Examples

### Mock DLT Source
```python
from cascade.testing import mock_dlt_source

test_data = [{"id": "1", "value": 42}]
with mock_dlt_source(data=test_data) as source:
    # Test your asset logic
    pass
```

### Fixture Management
```python
from cascade.testing import load_fixture, save_fixture

# Save fixture
save_fixture(test_data, "tests/fixtures/sample.json")

# Load fixture
data = load_fixture("tests/fixtures/sample.json")
```
"""

from cascade.testing.placeholders import (
    mock_dlt_source,
    mock_iceberg_catalog,
    test_asset_execution,
    MockDLTSource,
    MockIcebergCatalog,
    MockIcebergTable,
    MockTableScan,
    TestAssetResult,
    load_fixture,
    save_fixture,
)

__all__ = [
    # DLT Mocking (✅ Implemented)
    "mock_dlt_source",
    "MockDLTSource",
    # Iceberg Mocking (✅ Implemented)
    "mock_iceberg_catalog",
    "MockIcebergCatalog",
    "MockIcebergTable",
    "MockTableScan",
    # Asset Testing (✅ Implemented)
    "test_asset_execution",
    "TestAssetResult",
    # Fixture Management (✅ Implemented)
    "load_fixture",
    "save_fixture",
]

__version__ = "1.0.0"
