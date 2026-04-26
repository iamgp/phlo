"""Tests for workflow CLI commands."""

from pathlib import Path

from click.testing import CliRunner

from phlo.cli.main import cli


def test_authoring_commands_remain_discoverable() -> None:
    """Keeps the authoring path commands visible from root help."""
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "workflow" in result.output
    assert "schema" in result.output
    assert "validate-workflow" in result.output
    assert "materialize" in result.output
    assert "status" in result.output


def test_workflow_group_help_lists_create() -> None:
    """Shows the scaffold command in workflow group help output."""
    runner = CliRunner()
    result = runner.invoke(cli, ["workflow", "--help"])

    assert result.exit_code == 0
    assert "create" in result.output


def test_workflow_create_invokes_scaffold(monkeypatch) -> None:
    """Passes CLI options to ingestion scaffold creation."""
    calls = {}

    def fake_create_ingestion_workflow(
        *,
        domain: str,
        table_name: str,
        unique_key: str,
        cron: str,
        api_base_url: str | None,
        fields: list[str] | None,
    ) -> list[str]:
        """Captures scaffold arguments and returns mocked output paths.

        Args:
            domain: Domain passed from CLI option.
            table_name: Table name passed from CLI option.
            unique_key: Unique key passed from CLI option.
            cron: Cron schedule passed from CLI option.
            api_base_url: Optional API base URL from CLI option.
            fields: Optional field spec list from CLI option.

        Returns:
            list[str]: Relative paths representing scaffolded files.
        """
        calls.update(
            {
                "domain": domain,
                "table_name": table_name,
                "unique_key": unique_key,
                "cron": cron,
                "api_base_url": api_base_url,
                "fields": fields,
            }
        )
        return [
            "workflows/schemas/weather.py",
            "workflows/ingestion/weather/observations.py",
            "workflows/tests/weather/test_observations.py",
        ]

    monkeypatch.setattr(
        "phlo_dlt.scaffold.create_ingestion_workflow",
        fake_create_ingestion_workflow,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "workflow",
            "create",
            "--type",
            "ingestion",
            "--domain",
            "weather",
            "--table",
            "observations",
            "--unique-key",
            "id",
            "--cron",
            "0 */1 * * *",
            "--api-base-url",
            "https://api.example.com",
            "--field",
            "id:int",
        ],
    )

    assert result.exit_code == 0
    assert calls == {
        "domain": "weather",
        "table_name": "observations",
        "unique_key": "id",
        "cron": "0 */1 * * *",
        "api_base_url": "https://api.example.com",
        "fields": ["id:int"],
    }
    assert "Materialize: phlo materialize dlt_observations" in result.output


def test_workflow_create_converts_blank_api_base_url_to_none(monkeypatch) -> None:
    """Keeps optional API URL absent when the user accepts the blank prompt default."""
    calls = {}

    def fake_create_ingestion_workflow(**kwargs) -> list[str]:
        calls.update(kwargs)
        return [
            "workflows/schemas/events.py",
            "workflows/ingestion/events/clicks.py",
            "workflows/tests/events/test_clicks.py",
        ]

    monkeypatch.setattr(
        "phlo_dlt.scaffold.create_ingestion_workflow",
        fake_create_ingestion_workflow,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "workflow",
            "create",
            "--type",
            "ingestion",
            "--domain",
            "events",
            "--table",
            "clicks",
            "--unique-key",
            "event_id",
            "--cron",
            "0 0 * * *",
            "--api-base-url",
            "",
            "--field",
            "event_id:string!",
            "--field",
            "clicked_at:datetime?",
        ],
    )

    assert result.exit_code == 0
    assert calls["api_base_url"] is None
    assert calls["fields"] == ["event_id:string!", "clicked_at:datetime?"]
    assert "Review schema: workflows/schemas/events.py" in result.output


def test_workflow_create_prints_runnable_next_steps(monkeypatch, tmp_path) -> None:
    """Prints next steps that exist in the current CLI surface."""
    monkeypatch.chdir(tmp_path)

    def fake_create_ingestion_workflow(**kwargs):
        return [
            "workflows/schemas/weather.py",
            "workflows/ingestion/weather/observations.py",
            "tests/test_weather_observations.py",
        ]

    monkeypatch.setattr(
        "phlo_dlt.scaffold.create_ingestion_workflow",
        fake_create_ingestion_workflow,
    )

    result = CliRunner().invoke(
        cli,
        [
            "workflow",
            "create",
            "--type",
            "ingestion",
            "--domain",
            "weather",
            "--table",
            "observations",
            "--unique-key",
            "station_id",
            "--cron",
            "0 */1 * * *",
            "--api-base-url",
            "https://example.test",
        ],
    )

    assert result.exit_code == 0
    assert "phlo schema validate workflows/schemas/weather.py" in result.output
    assert "phlo validate-workflow workflows/ingestion/weather/observations.py" in result.output
    assert "phlo services restart dagster" in result.output
    assert "phlo materialize dlt_observations" in result.output
    assert "phlo test weather" not in result.output
    assert "docker restart" not in result.output


def test_workflow_create_reports_scaffold_failures(monkeypatch) -> None:
    """Exits with a concise error when scaffold creation fails."""

    def fake_create_ingestion_workflow(**kwargs) -> list[str]:
        raise RuntimeError("schema field is invalid")

    monkeypatch.setattr(
        "phlo_dlt.scaffold.create_ingestion_workflow",
        fake_create_ingestion_workflow,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "workflow",
            "create",
            "--type",
            "ingestion",
            "--domain",
            "weather",
            "--table",
            "observations",
            "--unique-key",
            "id",
            "--cron",
            "0 */1 * * *",
            "--api-base-url",
            "",
        ],
    )

    assert result.exit_code == 1
    assert "Error creating workflow: schema field is invalid" in result.output


def test_init_with_absolute_path_uses_directory_name_for_project_metadata(tmp_path: Path) -> None:
    """Uses directory basename, not full absolute path, for project name.

    Args:
        tmp_path: Temporary filesystem root for the test.
    """
    project_dir = tmp_path / "my-lakehouse"

    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(project_dir), "--template", "minimal"])

    assert result.exit_code == 0
    pyproject_content = (project_dir / "pyproject.toml").read_text()
    assert f'name = "{project_dir.name}"' in pyproject_content
    assert f'name = "{project_dir}"' not in pyproject_content
