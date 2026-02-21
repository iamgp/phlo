"""Tests for `phlo.exceptions` formatting and suggestion helpers."""

from __future__ import annotations

from phlo.exceptions import (
    PhloError,
    PhloErrorCode,
    format_field_list,
    suggest_similar_field_names,
)


def test_phlo_error_formats_message_with_code_suggestions_cause_and_docs() -> None:
    """Includes all rich formatting sections when suggestions and cause are present."""
    error = PhloError(
        message="Schema field missing",
        code=PhloErrorCode.SCHEMA_MISMATCH,
        suggestions=[
            "Check your validation schema",
            "Confirm field names match source data",
        ],
        cause=ValueError("missing field: observation_id"),
    )

    message = str(error)

    assert message.startswith("PhloError (PHLO-002): Schema field missing")
    assert "Suggested actions:" in message
    assert "  1. Check your validation schema" in message
    assert "  2. Confirm field names match source data" in message
    assert "Caused by: ValueError: missing field: observation_id" in message
    assert "Documentation: https://docs.phlo.dev/errors/PHLO-002" in message


def test_phlo_error_formats_minimal_message_without_optional_sections() -> None:
    """Omits suggestion/cause sections when not provided."""
    error = PhloError(
        message="DLT source failed",
        code=PhloErrorCode.DLT_SOURCE_ERROR,
    )

    message = str(error)

    assert "Suggested actions:" not in message
    assert "Caused by:" not in message
    assert message == (
        "PhloError (PHLO-301): DLT source failed\n\n"
        "Documentation: https://docs.phlo.dev/errors/PHLO-301"
    )


def test_suggest_similar_field_names_returns_fuzzy_matches() -> None:
    """Returns did-you-mean suggestions when close field matches exist."""
    suggestions = suggest_similar_field_names(
        invalid_field="temperatur",
        valid_fields=["temperature", "timestamp", "city", "humidity"],
        max_suggestions=2,
    )

    assert suggestions
    assert suggestions[0] == "Did you mean 'temperature'?"
    assert len(suggestions) <= 2
    assert all(suggestion.startswith("Did you mean '") for suggestion in suggestions)


def test_suggest_similar_field_names_returns_available_fields_when_no_match() -> None:
    """Falls back to listing available fields when fuzzy matching yields no results."""
    suggestions = suggest_similar_field_names(
        invalid_field="planet",
        valid_fields=["city", "country"],
    )

    assert suggestions == ["Available fields: city, country"]


def test_format_field_list_quotes_and_joins_fields() -> None:
    """Formats each field with single quotes and comma separators."""
    formatted = format_field_list(["id", "city", "temperature"])

    assert formatted == "'id', 'city', 'temperature'"


def test_format_field_list_handles_empty_field_list() -> None:
    """Returns an empty string when there are no fields."""
    formatted = format_field_list([])

    assert formatted == ""
