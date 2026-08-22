"""Unit tests for schema codegen helpers such as identifier snake-casing."""

from __future__ import annotations

from phlo_pandera.cli_schema_codegen import _snake_case


def test_snake_case_converts_camel_case_segments() -> None:
    """Verify camel-case segments are converted into snake_case."""
    assert _snake_case("MyTestCase") == "my_test_case"
    assert _snake_case("GitHubEvents") == "git_hub_events"
