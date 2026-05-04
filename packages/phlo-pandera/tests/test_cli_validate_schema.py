"""Tests for schema validation CLI behavior."""

from click.testing import CliRunner

from phlo_pandera.cli_validate import validate_schema


def test_validate_schema_rejects_files_without_schema_classes(tmp_path) -> None:
    schema_file = tmp_path / "empty.py"
    schema_file.write_text('"""Not a schema."""\n\nVALUE = 1\n')

    result = CliRunner().invoke(validate_schema, [str(schema_file)])

    assert result.exit_code != 0
    assert "No Pandera DataFrameModel classes found" in result.output
