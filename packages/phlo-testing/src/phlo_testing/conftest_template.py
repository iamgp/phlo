"""
Conftest template for user projects.

This module provides a ready-to-use conftest.py template that users can copy
to their tests/ directory to get all phlo_testing fixtures automatically.

Usage:
    from phlo_testing.conftest_template import CONFTEST_TEMPLATE

    # Write to tests/conftest.py
    Path("tests/conftest.py").write_text(CONFTEST_TEMPLATE)
"""

CONFTEST_TEMPLATE = '''"""
Pytest configuration and shared fixtures.

Place this file in tests/ directory to make fixtures available to all tests.
"""

import pytest
from pathlib import Path

# Import fixtures from phlo_testing
from phlo_testing.fixtures import (
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
'''


def get_conftest_template() -> str:
    """
    Get the conftest.py template content.

    Returns:
        String content for conftest.py
    """
    return CONFTEST_TEMPLATE
