"""Tests for JSONPlaceholder source plugin."""

import pytest
import responses

from phlo_example.source import JSONPlaceholderSource


@pytest.fixture
def plugin():
    """Create plugin instance."""
    return JSONPlaceholderSource()


@pytest.fixture
def valid_config():
    """Valid plugin configuration."""
    return {
        "base_url": "https://jsonplaceholder.typicode.com",
        "resource": "posts",
        "limit": 2,
    }


def test_metadata(plugin):
    """Test plugin metadata."""
    metadata = plugin.metadata
    assert metadata.name == "jsonplaceholder"
    assert metadata.version == "1.0.0"
    assert metadata.author == "Phlo Team"


def test_validate_config_valid(plugin, valid_config):
    """Test config validation with valid config."""
    assert plugin.validate_config(valid_config) is True


def test_validate_config_invalid_type(plugin):
    """Test config validation rejects non-dict."""
    assert plugin.validate_config("invalid") is False
    assert plugin.validate_config([]) is False


def test_validate_config_invalid_limit(plugin, valid_config):
    """Test config validation rejects invalid limit."""
    config = valid_config.copy()
    config["limit"] = -1
    assert plugin.validate_config(config) is False

    config["limit"] = "invalid"
    assert plugin.validate_config(config) is False


def test_get_schema(plugin, valid_config):
    """Test schema for posts resource."""
    schema = plugin.get_schema(valid_config)
    assert schema is not None
    assert "userId" in schema
    assert "title" in schema
    assert "body" in schema


def test_get_schema_comments(plugin):
    """Test schema for comments resource."""
    config = {"resource": "comments"}
    schema = plugin.get_schema(config)
    assert schema is not None
    assert "postId" in schema
    assert "email" in schema


def test_get_schema_unknown_resource(plugin):
    """Test schema for unknown resource returns None."""
    config = {"resource": "unknown"}
    schema = plugin.get_schema(config)
    assert schema is None


@responses.activate
def test_fetch_data(plugin, valid_config):
    """Test fetching data from API."""
    # Mock API response
    responses.add(
        responses.GET,
        "https://jsonplaceholder.typicode.com/posts",
        json=[
            {"userId": 1, "id": 1, "title": "Title 1", "body": "Body 1"},
            {"userId": 1, "id": 2, "title": "Title 2", "body": "Body 2"},
        ],
        status=200,
    )

    # Fetch data
    data = list(plugin.fetch_data(valid_config))

    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[1]["id"] == 2


@responses.activate
def test_fetch_data_respects_limit(plugin, valid_config):
    """Test that limit is respected."""
    # Mock API response with more items
    responses.add(
        responses.GET,
        "https://jsonplaceholder.typicode.com/posts",
        json=[
            {"userId": 1, "id": 1, "title": "Title 1", "body": "Body 1"},
            {"userId": 1, "id": 2, "title": "Title 2", "body": "Body 2"},
            {"userId": 1, "id": 3, "title": "Title 3", "body": "Body 3"},
        ],
        status=200,
    )

    # Fetch with limit
    valid_config["limit"] = 2
    data = list(plugin.fetch_data(valid_config))

    assert len(data) == 2


@responses.activate
def test_fetch_data_no_limit(plugin, valid_config):
    """Test fetching all data when limit is 0."""
    responses.add(
        responses.GET,
        "https://jsonplaceholder.typicode.com/posts",
        json=[
            {"id": 1},
            {"id": 2},
            {"id": 3},
        ],
        status=200,
    )

    valid_config["limit"] = 0
    data = list(plugin.fetch_data(valid_config))

    assert len(data) == 3


@responses.activate
def test_fetch_data_invalid_config(plugin):
    """Test fetching with invalid config raises error."""
    config = {"base_url": 123}  # Invalid: not a string

    with pytest.raises(ValueError):
        list(plugin.fetch_data(config))


@responses.activate
def test_fetch_data_api_error(plugin, valid_config):
    """Test handling of API errors."""
    responses.add(
        responses.GET,
        "https://jsonplaceholder.typicode.com/posts",
        status=500,
    )

    with pytest.raises(RuntimeError):
        list(plugin.fetch_data(valid_config))


@responses.activate
def test_test_connection_success(plugin, valid_config):
    """Test successful connection test."""
    responses.add(
        responses.GET,
        "https://jsonplaceholder.typicode.com/posts",
        json=[],
        status=200,
    )

    assert plugin.test_connection(valid_config) is True


@responses.activate
def test_test_connection_failure(plugin, valid_config):
    """Test failed connection test."""
    responses.add(
        responses.GET,
        "https://jsonplaceholder.typicode.com/posts",
        status=500,
    )

    assert plugin.test_connection(valid_config) is False
