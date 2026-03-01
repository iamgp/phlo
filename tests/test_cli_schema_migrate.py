"""Regression tests for schema-migrate CLI commands."""

import json
from pathlib import Path

import yaml
from click.testing import CliRunner

from phlo.capabilities.specs import FieldSpec, NormalizedSchema, SchemaChange, SchemaMigrationPlan
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


def _patch_schema_resolution(monkeypatch) -> None:
    class FakeExtractor:
        def extract(self, native_schema: object) -> NormalizedSchema:
            return NormalizedSchema(
                fields=[
                    FieldSpec(name="id", dtype="int64", nullable=False),
                    FieldSpec(name="name", dtype="string", nullable=True),
                ],
            )

    class FakeMigrator:
        def diff_schema(self, *, table_name: str, desired: NormalizedSchema) -> SchemaMigrationPlan:
            assert table_name == "warehouse.customers"
            assert len(desired.fields) >= 1
            return SchemaMigrationPlan(
                table_name=table_name,
                changes=[
                    SchemaChange(
                        field_name="name",
                        change_type="add",
                        new_value="string",
                        classification="safe",
                    )
                ],
                classification="safe",
                recommendations=[],
                requires_approval=False,
            )

    class CustomerSchema:
        __name__ = "CustomerSchema"

    monkeypatch.setattr(schema_migrate_commands, "_resolve_extractor", lambda: FakeExtractor())
    monkeypatch.setattr(schema_migrate_commands, "_resolve_migrator", lambda: FakeMigrator())
    monkeypatch.setattr(
        schema_migrate_commands,
        "_find_native_schema",
        lambda table_name, schema_class: CustomerSchema,
    )
    monkeypatch.setattr(
        schema_migrate_commands, "_select_default_table_store_name", lambda: "iceberg"
    )
    monkeypatch.setattr(schema_migrate_commands, "_select_default_migrator_name", lambda: "iceberg")
    monkeypatch.setattr(schema_migrate_commands, "_collect_quality_checks", lambda table_name: [])
    monkeypatch.setattr(schema_migrate_commands, "_collect_transform_refs", lambda table_name: [])


def test_schema_migrate_export_contract_writes_default_path(monkeypatch) -> None:
    """Writes a contract file to default location."""
    _patch_schema_resolution(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["schema-migrate", "export-contract", "warehouse.customers"])
        assert result.exit_code == 0

        contract_path = Path(".phlo/contracts/warehouse__customers.json")
        assert contract_path.exists()
        payload = json.loads(contract_path.read_text(encoding="utf-8"))
        assert payload["table_name"] == "warehouse.customers"
        assert payload["schema_migrator"] == "iceberg"
        assert payload["contract_version"] == 1


def test_schema_migrate_scaffold_yaml_reads_contract(monkeypatch) -> None:
    """Generates migration scaffold YAML from an existing contract file."""
    _patch_schema_resolution(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem():
        export_result = runner.invoke(
            cli, ["schema-migrate", "export-contract", "warehouse.customers"]
        )
        assert export_result.exit_code == 0

        result = runner.invoke(cli, ["schema-migrate", "scaffold-yaml", "warehouse.customers"])
        assert result.exit_code == 0

        yaml_path = Path(".phlo/migrations/warehouse__customers.yaml")
        assert yaml_path.exists()
        payload = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        assert payload["table_name"] == "warehouse.customers"
        assert payload["classification"] == "safe"
        assert payload["operations"][0]["change_type"] == "add"
        assert payload["operations"][0]["operation_id"]


def test_schema_migrate_scaffold_yaml_is_deterministic(monkeypatch) -> None:
    """Stable operation IDs are emitted for identical plans."""
    _patch_schema_resolution(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem():
        contract_path = Path(".phlo/contracts/warehouse__customers.json")
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        contract_path.write_text(
            json.dumps(
                {
                    "contract_version": 1,
                    "table_name": "warehouse.customers",
                    "normalized_schema": {
                        "fields": [
                            {
                                "name": "id",
                                "dtype": "int64",
                                "nullable": False,
                                "default": None,
                                "metadata": {},
                            }
                        ],
                        "metadata": {},
                    },
                    "quality_checks": [],
                    "transform_refs": [],
                }
            ),
            encoding="utf-8",
        )

        first = runner.invoke(cli, ["schema-migrate", "scaffold-yaml", "warehouse.customers"])
        assert first.exit_code == 0
        first_yaml = yaml.safe_load(Path(".phlo/migrations/warehouse__customers.yaml").read_text())
        first_operation_id = first_yaml["operations"][0]["operation_id"]

        second = runner.invoke(
            cli, ["schema-migrate", "scaffold-yaml", "warehouse.customers", "--force"]
        )
        assert second.exit_code == 0
        second_yaml = yaml.safe_load(Path(".phlo/migrations/warehouse__customers.yaml").read_text())
        assert second_yaml["operations"][0]["operation_id"] == first_operation_id
