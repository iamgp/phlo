"""Tests for workflow CLI commands."""

from click.testing import CliRunner

from phlo.cli.main import cli


def test_workflow_group_help_lists_create() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["workflow", "--help"])

    assert result.exit_code == 0
    assert "create" in result.output


def test_workflow_create_invokes_scaffold(monkeypatch) -> None:
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
        return ["workflows/schemas/weather.py", "workflows/ingestion/weather/observations.py"]

    monkeypatch.setattr(
        "phlo.cli.scaffold.create_ingestion_workflow",
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
