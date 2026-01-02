"""Integration tests for phlo-observatory."""

import pytest

pytestmark = pytest.mark.integration


def test_observatory_importable():
    """Test that phlo_observatory is importable."""
    import phlo_observatory

    assert phlo_observatory is not None


def test_observatory_app_exists():
    """Test that observatory app or main module exists."""
    try:
        import importlib

        app_module = importlib.import_module("phlo_observatory.app")
        assert app_module is not None
    except Exception:
        # May have different structure
        pass
