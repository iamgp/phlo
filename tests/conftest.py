"""
Pytest configuration and shared fixtures for Phlo tests.

This conftest.py imports fixtures from phlo.testing and makes them available
to all tests in the tests/ directory.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import fixtures from phlo.testing - these are auto-discovered by pytest
from phlo.testing.fixtures import (
    mock_iceberg_catalog,
    mock_trino,
    mock_asset_context,
    mock_resources,
    sample_partition_date,
    sample_partition_range,
    sample_dlt_data,
    sample_dataframe,
    mock_dlt_source_fixture,
    temp_staging_dir,
    test_data_dir,
    setup_test_catalog,
    setup_test_trino,
    load_json_fixture,
    load_csv_fixture,
    test_config,
)


@pytest.fixture(autouse=True)
def reset_test_env(monkeypatch):
    """Reset environment variables before each test."""
    monkeypatch.setenv("PHLO_ENV", "test")
    monkeypatch.setenv("PHLO_LOG_LEVEL", "DEBUG")


@pytest.fixture
def project_root() -> Path:
    """Return path to project root."""
    return Path(__file__).parent.parent
