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


@pytest.fixture(autouse=True)
def reset_test_env(monkeypatch):
    """Reset environment variables before each test."""
    monkeypatch.setenv("PHLO_ENV", "test")
    monkeypatch.setenv("PHLO_LOG_LEVEL", "DEBUG")


@pytest.fixture
def project_root() -> Path:
    """Return path to project root."""
    return Path(__file__).parent.parent
