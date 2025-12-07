"""Tests for threshold quality check plugin."""

import pandas as pd
import pytest

from phlo_example.quality import ThresholdCheckPlugin


@pytest.fixture
def plugin():
    """Create plugin instance."""
    return ThresholdCheckPlugin()


@pytest.fixture
def sample_df():
    """Create sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "value": [10, 50, 100, 150, 200],
            "name": ["a", "b", "c", "d", "e"],
        }
    )


def test_metadata(plugin):
    """Test plugin metadata."""
    metadata = plugin.metadata
    assert metadata.name == "threshold_check"
    assert metadata.version == "1.0.0"


def test_create_check(plugin):
    """Test creating a threshold check."""
    check = plugin.create_check(
        column="value",
        min=0,
        max=100,
        tolerance=0.0,
    )

    assert check.column == "value"
    assert check.min_value == 0
    assert check.max_value == 100
    assert check.tolerance == 0.0


def test_check_name(plugin):
    """Test check name generation."""
    check = plugin.create_check(
        column="value",
        min=0,
        max=100,
    )

    assert "threshold_check" in check.name
    assert "value" in check.name


def test_check_within_bounds(plugin, sample_df):
    """Test check passes when all values are within bounds."""
    check = plugin.create_check(
        column="value",
        min=0,
        max=250,
        tolerance=0.0,
    )

    result = check.execute(sample_df)

    assert result["passed"] is True
    assert result["violations"] == 0
    assert result["violation_rate"] == 0.0


def test_check_violations(plugin, sample_df):
    """Test check detects violations."""
    check = plugin.create_check(
        column="value",
        min=0,
        max=100,
        tolerance=0.0,
    )

    result = check.execute(sample_df)

    assert result["passed"] is False
    assert result["violations"] == 2  # 150, 200
    assert result["total"] == 5


def test_check_with_tolerance(plugin, sample_df):
    """Test check with tolerance threshold."""
    check = plugin.create_check(
        column="value",
        min=0,
        max=100,
        tolerance=0.5,  # Allow 50% violations
    )

    result = check.execute(sample_df)

    assert result["passed"] is True
    assert result["violations"] == 2
    assert result["violation_rate"] == 0.4  # 2/5


def test_check_missing_column(plugin, sample_df):
    """Test check handles missing column."""
    check = plugin.create_check(
        column="nonexistent",
        min=0,
        max=100,
    )

    result = check.execute(sample_df)

    assert result["passed"] is False
    assert result["violations"] == len(sample_df)
    assert "error" in result


def test_check_with_nulls(plugin):
    """Test check handles null values."""
    df = pd.DataFrame(
        {
            "value": [10, 50, None, 150, 200],
        }
    )

    check = plugin.create_check(
        column="value",
        min=0,
        max=100,
        tolerance=0.0,
    )

    result = check.execute(df)

    assert result["passed"] is False
    assert result["violations"] == 3  # None, 150, 200


def test_check_min_only(plugin, sample_df):
    """Test check with only minimum bound."""
    check = plugin.create_check(
        column="value",
        min=100,
    )

    result = check.execute(sample_df)

    assert result["passed"] is False
    assert result["violations"] == 2  # 10, 50


def test_check_max_only(plugin, sample_df):
    """Test check with only maximum bound."""
    check = plugin.create_check(
        column="value",
        max=100,
    )

    result = check.execute(sample_df)

    assert result["passed"] is False
    assert result["violations"] == 2  # 150, 200


def test_check_tolerance_clamping(plugin):
    """Test that tolerance is clamped to 0.0-1.0."""
    check1 = plugin.create_check(
        column="value",
        tolerance=-0.5,
    )
    assert check1.tolerance == 0.0

    check2 = plugin.create_check(
        column="value",
        tolerance=1.5,
    )
    assert check2.tolerance == 1.0
