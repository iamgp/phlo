"""
Pytest configuration and shared fixtures for Phlo tests.

This conftest.py imports fixtures from phlo_testing and makes them available
to all tests in the repository.
"""

import importlib
import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Add workspace package sources for local test runs (monorepo layout)
packages_dir = Path(__file__).parent / "packages"
if packages_dir.exists():
    for package_src in packages_dir.glob("*/src"):
        if str(package_src) not in sys.path:
            sys.path.insert(0, str(package_src))


def _register_workspace_plugins() -> None:
    try:
        registry_module = importlib.import_module("phlo.plugins.registry")
        dlt_module = importlib.import_module("phlo_dlt.plugin")
    except Exception:
        return

    registry = registry_module.get_global_registry()
    registry.register_dagster_extension(dlt_module.DltDagsterPlugin(), replace=True)


_register_workspace_plugins()

# Import fixtures from phlo_testing - these are auto-discovered by pytest


@pytest.fixture(autouse=True)
def reset_test_env(monkeypatch):
    """Reset environment variables before each test."""
    monkeypatch.setenv("PHLO_ENV", "test")
    monkeypatch.setenv("PHLO_LOG_LEVEL", "DEBUG")


@pytest.fixture
def project_root() -> Path:
    """Return path to project root."""
    return Path(__file__).parent
