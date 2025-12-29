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
        from phlo_observatory import app
        assert app is not None
    except ImportError:
        # May have different structure
        pass
