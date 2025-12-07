"""Tests for uppercase transformation plugin."""

import pandas as pd
import pytest

from phlo_example.transform import UppercaseTransformPlugin


@pytest.fixture
def plugin():
    """Create plugin instance."""
    return UppercaseTransformPlugin()


@pytest.fixture
def sample_df():
    """Create sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "title": ["hello world", "foo bar", "test"],
            "body": ["this is a test", "another test", "final test"],
        }
    )


def test_metadata(plugin):
    """Test plugin metadata."""
    metadata = plugin.metadata
    assert metadata.name == "uppercase"
    assert metadata.version == "1.0.0"


def test_validate_config_valid(plugin):
    """Test config validation with valid config."""
    config = {
        "columns": ["title", "body"],
        "skip_na": True,
    }
    assert plugin.validate_config(config) is True


def test_validate_config_invalid_type(plugin):
    """Test config validation rejects non-dict."""
    assert plugin.validate_config("invalid") is False
    assert plugin.validate_config([]) is False


def test_validate_config_invalid_columns(plugin):
    """Test config validation rejects invalid columns."""
    # Not a list
    config = {"columns": "title"}
    assert plugin.validate_config(config) is False

    # Contains non-string
    config = {"columns": ["title", 123]}
    assert plugin.validate_config(config) is False


def test_validate_config_invalid_skip_na(plugin):
    """Test config validation rejects invalid skip_na."""
    config = {
        "columns": ["title"],
        "skip_na": "yes",  # Should be boolean
    }
    assert plugin.validate_config(config) is False


def test_transform_single_column(plugin, sample_df):
    """Test transforming a single column."""
    config = {
        "columns": ["title"],
        "skip_na": True,
    }

    result = plugin.transform(sample_df, config)

    assert result["title"].iloc[0] == "HELLO WORLD"
    assert result["title"].iloc[1] == "FOO BAR"
    assert result["body"].iloc[0] == "this is a test"  # Unchanged


def test_transform_multiple_columns(plugin, sample_df):
    """Test transforming multiple columns."""
    config = {
        "columns": ["title", "body"],
        "skip_na": True,
    }

    result = plugin.transform(sample_df, config)

    assert result["title"].iloc[0] == "HELLO WORLD"
    assert result["body"].iloc[0] == "THIS IS A TEST"


def test_transform_preserves_other_columns(plugin, sample_df):
    """Test that non-transformed columns are unchanged."""
    config = {
        "columns": ["title"],
        "skip_na": True,
    }

    result = plugin.transform(sample_df, config)

    pd.testing.assert_series_equal(result["id"], sample_df["id"], check_names=True)


def test_transform_with_nulls_skip_na_true(plugin):
    """Test handling of null values with skip_na=True."""
    df = pd.DataFrame(
        {
            "text": ["hello", None, "world"],
        }
    )

    config = {
        "columns": ["text"],
        "skip_na": True,
    }

    result = plugin.transform(df, config)

    assert result["text"].iloc[0] == "HELLO"
    assert pd.isna(result["text"].iloc[1])
    assert result["text"].iloc[2] == "WORLD"


def test_transform_with_nulls_skip_na_false(plugin):
    """Test handling of null values with skip_na=False."""
    df = pd.DataFrame(
        {
            "text": ["hello", None, "world"],
        }
    )

    config = {
        "columns": ["text"],
        "skip_na": False,
    }

    # This will raise an error because None.str.upper() is invalid
    with pytest.raises(AttributeError):
        plugin.transform(df, config)


def test_transform_missing_column(plugin, sample_df):
    """Test error when transforming non-existent column."""
    config = {
        "columns": ["nonexistent"],
        "skip_na": True,
    }

    with pytest.raises(ValueError, match="not found"):
        plugin.transform(sample_df, config)


def test_transform_invalid_config(plugin, sample_df):
    """Test error with invalid configuration."""
    config = {
        "columns": "title",  # Should be list
        "skip_na": True,
    }

    with pytest.raises(ValueError, match="Invalid configuration"):
        plugin.transform(sample_df, config)


def test_transform_does_not_modify_original(plugin, sample_df):
    """Test that transformation doesn't modify original DataFrame."""
    original = sample_df.copy()
    config = {
        "columns": ["title"],
        "skip_na": True,
    }

    plugin.transform(sample_df, config)

    pd.testing.assert_frame_equal(sample_df, original)


def test_get_output_schema(plugin):
    """Test output schema is same as input."""
    input_schema = {
        "title": "string",
        "body": "string",
        "id": "int",
    }

    config = {
        "columns": ["title", "body"],
    }

    output_schema = plugin.get_output_schema(input_schema, config)

    assert output_schema == input_schema
