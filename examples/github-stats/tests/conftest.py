"""
Pytest configuration and shared fixtures.

This conftest imports phlo_testing fixtures so all tests can use mocked
resources without Docker dependencies.
"""

from pathlib import Path

import pytest

# Import phlo_testing fixtures - these provide mocked Iceberg, Trino, DLT
from phlo_testing.fixtures import (
    load_json_fixture,
    mock_asset_context,
    mock_dlt_source_fixture,
    mock_iceberg_catalog,
    mock_resources,
    mock_trino,
    sample_dataframe,
    sample_dlt_data,
    sample_partition_date,
    sample_partition_range,
    temp_staging_dir,
)

# Re-export so pytest autodiscovers them
__all__ = [
    "mock_iceberg_catalog",
    "mock_trino",
    "mock_asset_context",
    "mock_resources",
    "sample_partition_date",
    "sample_partition_range",
    "sample_dlt_data",
    "sample_dataframe",
    "mock_dlt_source_fixture",
    "temp_staging_dir",
    "load_json_fixture",
    "project_root",
    "reset_test_env",
]


@pytest.fixture(autouse=True)
def reset_test_env(monkeypatch):
    """Reset environment variables before each test."""
    monkeypatch.setenv("PHLO_ENV", "test")
    monkeypatch.setenv("PHLO_LOG_LEVEL", "DEBUG")


@pytest.fixture
def project_root() -> Path:
    """Return path to project root."""
    return Path(__file__).parent.parent
