"""Regression tests for schema-migrate CLI commands."""

from click.testing import CliRunner

from phlo.cli.commands import schema_migrate as schema_migrate_commands
from phlo.cli.main import cli


def test_schema_migrate_history_renders_timestamp_ms(monkeypatch) -> None:
    """Renders snapshot timestamp when migrator returns timestamp_ms keys."""

    class FakeMigrator:
        def get_schema_history(
            self, *, table_name: str, limit: int = 10
        ) -> list[dict[str, object]]:
            assert table_name == "warehouse.customers"
            assert limit == 5
            return [
                {
                    "snapshot_id": 123,
                    "timestamp_ms": 1709251200000,
                    "summary": {"operation": "append"},
                }
            ]

    monkeypatch.setattr(schema_migrate_commands, "_resolve_migrator", lambda: FakeMigrator())

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["schema-migrate", "history", "warehouse.customers", "--limit", "5"],
    )

    assert result.exit_code == 0
    assert "1709251200000" in result.output
    assert "123" in result.output
