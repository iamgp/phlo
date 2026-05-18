"""Regression tests for data migration CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from phlo.cli.commands import migrate as migrate_commands
from phlo.cli.main import cli


def _write_csv(path: Path) -> None:
    path.write_text("id,email_addr\n1,a@example.com\n2,b@example.com\n", encoding="utf-8")


def _write_spec(path: Path, *, dry_run: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "name: initial_load_customers",
                'version: "1.0"',
                "description: migrate customers",
                "source:",
                "  type: csv",
                "  path: ./customers.csv",
                "destination:",
                "  table: warehouse.customers",
                "  write_mode: append",
                "options:",
                "  chunk_size: 1",
                f"  dry_run: {'true' if dry_run else 'false'}",
                "column_mapping:",
                "  email_addr: email",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_migrate_validate_passes_for_dry_run_csv() -> None:
    """Validate command accepts minimal dry-run CSV spec."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write_csv(Path("customers.csv"))
        _write_spec(Path("migrations/customers.yaml"), dry_run=True)

        result = runner.invoke(cli, ["migrate", "validate", "migrations/customers.yaml"])

        assert result.exit_code == 0
        assert "Migration spec is valid" in result.output


def test_migrate_validate_uses_dry_run_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate command always validates as dry-run to avoid table-store requirements."""

    class FakeExecutor:
        seen_override: bool | None = None

        def validate(self, spec, *, dry_run_override=None):  # type: ignore[no-untyped-def]
            FakeExecutor.seen_override = dry_run_override
            return []

    monkeypatch.setattr(migrate_commands, "MigrationExecutor", lambda: FakeExecutor())

    runner = CliRunner()
    with runner.isolated_filesystem():
        _write_csv(Path("customers.csv"))
        _write_spec(Path("migrations/customers.yaml"), dry_run=False)

        result = runner.invoke(cli, ["migrate", "validate", "migrations/customers.yaml"])

        assert result.exit_code == 0
        assert FakeExecutor.seen_override is True


def test_migrate_run_dry_run_writes_history() -> None:
    """Run command executes dry-run migration and records history."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write_csv(Path("customers.csv"))
        _write_spec(Path("migrations/customers.yaml"), dry_run=True)

        result = runner.invoke(
            cli,
            ["migrate", "run", "migrations/customers.yaml", "--format", "json"],
        )
        assert result.exit_code == 0

        payload = json.loads(result.output)
        assert payload["status"] == "dry_run"
        assert payload["rows_read"] == 2
        assert payload["rows_written"] == 0

        history_path = Path(".phlo/migrations/history.jsonl")
        assert history_path.exists()
        entries = [
            json.loads(line) for line in history_path.read_text(encoding="utf-8").splitlines()
        ]
        assert entries[-1]["name"] == "initial_load_customers"


def test_migrate_list_reads_default_directories() -> None:
    """List command returns migration YAML files from default directories."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("migrations").mkdir(parents=True, exist_ok=True)
        Path("workflows/migrations").mkdir(parents=True, exist_ok=True)
        Path("migrations/a.yaml").write_text("name: a\n", encoding="utf-8")
        Path("workflows/migrations/b.yml").write_text("name: b\n", encoding="utf-8")

        result = runner.invoke(cli, ["migrate", "list"])

        assert result.exit_code == 0
        assert "migrations/a.yaml" in result.output
        assert "workflows/migrations/b.yml" in result.output


def test_migrate_status_reads_history_table() -> None:
    """Status command renders recent migration history."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path(".phlo/migrations").mkdir(parents=True, exist_ok=True)
        Path(".phlo/migrations/history.jsonl").write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "name": "initial_load_customers",
                            "status": "dry_run",
                            "rows_read": 2,
                            "rows_written": 0,
                            "rows_rejected": 0,
                            "chunks_processed": 2,
                            "duration_seconds": 0.12,
                            "validation_passed": None,
                            "metadata": {"timestamp": "2026-03-01T00:00:00+00:00"},
                        }
                    )
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(cli, ["migrate", "status", "--limit", "5", "--format", "json"])

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload[0]["name"] == "initial_load_customers"
        assert payload[0]["status"] == "dry_run"


def test_migrate_provider_api_check_reports_needed_changes() -> None:
    """Provider API check mode should report legacy provider-coupled API usage."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_path = Path("workflows/events.py")
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        workflow_path.write_text(
            "\n".join(
                [
                    "from phlo_dlt import phlo_ingestion",
                    "",
                    "",
                    '@phlo_ingestion(table_name="events")',
                    "def events():",
                    "    pass",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        result = runner.invoke(cli, ["migrate", "provider-api", "workflows", "--check"])

        assert result.exit_code == 1
        assert "Provider API migration needed" in result.output
        assert "workflows/events.py" in result.output
        assert "from phlo_dlt import phlo_ingestion" in workflow_path.read_text(encoding="utf-8")


def test_migrate_provider_api_write_updates_files() -> None:
    """Provider API write mode should update legacy imports and decorator calls."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_path = Path("events.py")
        workflow_path.write_text(
            "\n".join(
                [
                    "from phlo_dlt import phlo_ingestion",
                    "",
                    "",
                    '@phlo_ingestion(table_name="events")',
                    "def events():",
                    "    pass",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        result = runner.invoke(cli, ["migrate", "provider-api", "events.py", "--write"])

        assert result.exit_code == 0
        assert "Updated 1 file" in result.output
        assert "@phlo.ingest.dlt" in workflow_path.read_text(encoding="utf-8")


def test_migrate_provider_api_check_passes_when_no_changes_needed() -> None:
    """Provider API check mode should pass when files already use the neutral API."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_path = Path("events.py")
        workflow_path.write_text(
            "\n".join(
                [
                    "import phlo",
                    "",
                    "",
                    '@phlo.ingest.dlt(table_name="events")',
                    "def events():",
                    "    pass",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        result = runner.invoke(cli, ["migrate", "provider-api", "events.py", "--check"])

        assert result.exit_code == 0
        assert "No provider API migrations needed" in result.output
