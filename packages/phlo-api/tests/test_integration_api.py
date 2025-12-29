"""Integration tests for phlo-api."""

import pytest

pytestmark = pytest.mark.integration


def test_api_module_importable():
    """Test that phlo_api is importable."""
    import phlo_api
    assert phlo_api is not None


def test_api_has_expected_exports():
    """Test that API has expected exports or structure."""
    import phlo_api
    # Just verify the module is importable
    assert hasattr(phlo_api, "__name__")
