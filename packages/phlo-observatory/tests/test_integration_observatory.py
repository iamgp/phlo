"""Unit tests for phlo-observatory import surface."""

import importlib

import pytest

pytestmark = pytest.mark.unit


def test_observatory_importable():
    """Test that phlo_observatory is importable."""
    import phlo_observatory

    assert phlo_observatory is not None


def test_observatory_plugin_module_importable():
    """Test that the service plugin module is importable."""
    plugin_module = importlib.import_module("phlo_observatory.plugin")
    assert plugin_module is not None


def test_observatory_app_module_absent():
    """Test that legacy app module is not exposed by this package."""
    with pytest.raises(ModuleNotFoundError, match="phlo_observatory.app"):
        importlib.import_module("phlo_observatory.app")
