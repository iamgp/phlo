"""Regression tests for schema-migrate CLI commands."""

import json
import os
import sys
import types
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from phlo.capabilities.specs import (
    FieldSpec,
    NormalizedSchema,
    SchemaChange,
    SchemaMigrationPlan,
    SchemaMigrationSpec,
)
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


def test_resolve_migrator_prefers_matching_table_store_default(monkeypatch) -> None:
    """Schema migrator follows the configured table_store when names align."""

    iceberg_migrator = object()
    delta_migrator = object()

    class FakeRegistry:
        def list_schema_migrators(self) -> list[SchemaMigrationSpec]:
            return [
                SchemaMigrationSpec(name="delta", provider=delta_migrator),
                SchemaMigrationSpec(name="iceberg", provider=iceberg_migrator),
            ]

    monkeypatch.setattr(schema_migrate_commands, "get_capability_registry", lambda: FakeRegistry())
    monkeypatch.setattr(
        schema_migrate_commands,
        "configured_capability_name",
        lambda capability_type: None if capability_type == "schema_migrator" else "iceberg",
    )
    monkeypatch.setattr("phlo.capabilities.discovery.discover_capabilities", lambda: None)

    resolved = schema_migrate_commands._resolve_migrator()

    assert resolved is iceberg_migrator


def test_resolve_migrator_prefers_explicit_schema_migrator_default(monkeypatch) -> None:
    """Explicit schema_migrator config wins over table_store-derived selection."""

    iceberg_migrator = object()
    delta_migrator = object()

    class FakeRegistry:
        def list_schema_migrators(self) -> list[SchemaMigrationSpec]:
            return [
                SchemaMigrationSpec(name="delta", provider=delta_migrator),
                SchemaMigrationSpec(name="iceberg", provider=iceberg_migrator),
            ]

    monkeypatch.setattr(schema_migrate_commands, "get_capability_registry", lambda: FakeRegistry())
    monkeypatch.setattr(
        schema_migrate_commands,
        "configured_capability_name",
        lambda capability_type: "delta" if capability_type == "schema_migrator" else "iceberg",
    )
    monkeypatch.setattr("phlo.capabilities.discovery.discover_capabilities", lambda: None)

    resolved = schema_migrate_commands._resolve_migrator()

    assert resolved is delta_migrator


def test_resolve_migrator_fails_when_configured_schema_migrator_missing(monkeypatch) -> None:
    """Missing explicit schema_migrator config errors deterministically."""

    class FakeRegistry:
        def list_schema_migrators(self) -> list[SchemaMigrationSpec]:
            return [SchemaMigrationSpec(name="iceberg", provider=object())]

    monkeypatch.setattr(schema_migrate_commands, "get_capability_registry", lambda: FakeRegistry())
    monkeypatch.setattr(
        schema_migrate_commands,
        "configured_capability_name",
        lambda capability_type: "delta" if capability_type == "schema_migrator" else None,
    )
    monkeypatch.setattr(
        schema_migrate_commands,
        "list_capabilities",
        lambda capability_type: ["iceberg"] if capability_type == "schema_migrator" else [],
    )
    monkeypatch.setattr("phlo.capabilities.discovery.discover_capabilities", lambda: None)

    with pytest.raises(SystemExit) as exc_info:
        schema_migrate_commands._resolve_migrator()

    assert exc_info.value.code == 1


def test_resolve_migrator_fails_when_multiple_installed_without_selection(monkeypatch) -> None:
    """Ambiguous schema migrators require config instead of first-provider fallback."""

    class FakeRegistry:
        def list_schema_migrators(self) -> list[SchemaMigrationSpec]:
            return [
                SchemaMigrationSpec(name="delta", provider=object()),
                SchemaMigrationSpec(name="iceberg", provider=object()),
            ]

    monkeypatch.setattr(schema_migrate_commands, "get_capability_registry", lambda: FakeRegistry())
    monkeypatch.setattr(
        schema_migrate_commands,
        "configured_capability_name",
        lambda capability_type: None,
    )
    monkeypatch.setattr(
        schema_migrate_commands,
        "list_capabilities",
        lambda capability_type: (
            ["delta", "iceberg"] if capability_type == "schema_migrator" else []
        ),
    )
    monkeypatch.setattr("phlo.capabilities.discovery.discover_capabilities", lambda: None)

    with pytest.raises(SystemExit) as exc_info:
        schema_migrate_commands._resolve_migrator()

    assert exc_info.value.code == 1


def test_resolve_migrator_reports_table_store_mismatch_when_ambiguous(monkeypatch) -> None:
    """Ambiguous error explains when configured table_store did not match any migrator."""

    class FakeRegistry:
        def list_schema_migrators(self) -> list[SchemaMigrationSpec]:
            return [
                SchemaMigrationSpec(name="delta", provider=object()),
                SchemaMigrationSpec(name="iceberg", provider=object()),
            ]

    monkeypatch.setattr(schema_migrate_commands, "get_capability_registry", lambda: FakeRegistry())
    monkeypatch.setattr(
        schema_migrate_commands,
        "configured_capability_name",
        lambda capability_type: None if capability_type == "schema_migrator" else "delta_lake",
    )
    monkeypatch.setattr(
        schema_migrate_commands,
        "list_capabilities",
        lambda capability_type: (
            ["delta", "iceberg"] if capability_type == "schema_migrator" else []
        ),
    )
    monkeypatch.setattr("phlo.capabilities.discovery.discover_capabilities", lambda: None)

    with pytest.raises(SystemExit) as exc_info:
        schema_migrate_commands._resolve_migrator()

    assert exc_info.value.code == 1


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
    monkeypatch.setattr(
        schema_migrate_commands,
        "_collect_contract_metadata",
        lambda table_name: {
            "owner": "platform-team",
            "consumers": [{"name": "analytics", "contact": "#analytics", "usage": None}],
            "sla": {"quality_threshold": 0.99},
        },
    )
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
        assert payload["contract_metadata"]["owner"] == "platform-team"


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


def test_schema_migrate_scaffold_yaml_recent_reads_recent_contracts(monkeypatch) -> None:
    """Scaffold recent contract additions into migration YAML files."""
    _patch_schema_resolution(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem():
        contracts_dir = Path(".phlo/contracts")
        contracts_dir.mkdir(parents=True, exist_ok=True)

        recent_contract = contracts_dir / "warehouse__customers.json"
        recent_contract.write_text(
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

        stale_contract = contracts_dir / "warehouse__orders.json"
        stale_contract.write_text(
            json.dumps(
                {
                    "contract_version": 1,
                    "table_name": "warehouse.orders",
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
        stale_ts = recent_contract.stat().st_mtime - (48 * 3600)
        os.utime(stale_contract, (stale_ts, stale_ts))

        result = runner.invoke(
            cli,
            ["schema-migrate", "scaffold-yaml-recent", "--since-hours", "24"],
        )
        assert result.exit_code == 0
        assert "Generated 1 migration scaffolds." in result.output

        assert Path(".phlo/migrations/warehouse__customers.yaml").exists()
        assert not Path(".phlo/migrations/warehouse__orders.yaml").exists()


def test_schema_migrate_scaffold_yaml_recent_continues_after_error(monkeypatch) -> None:
    """Recent scaffold continues processing valid contracts after per-item failures."""
    _patch_schema_resolution(monkeypatch)
    runner = CliRunner()
    with runner.isolated_filesystem():
        contracts_dir = Path(".phlo/contracts")
        contracts_dir.mkdir(parents=True, exist_ok=True)

        valid_contract = contracts_dir / "warehouse__customers.json"
        valid_contract.write_text(
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

        broken_contract = contracts_dir / "warehouse__broken.json"
        broken_contract.write_text("{not-json}", encoding="utf-8")

        result = runner.invoke(
            cli,
            ["schema-migrate", "scaffold-yaml-recent", "--since-hours", "24"],
        )
        assert result.exit_code == 1
        assert "Generated 1 migration scaffolds." in result.output
        assert "Encountered 1 errors while scaffolding recent contracts." in result.output
        assert Path(".phlo/migrations/warehouse__customers.yaml").exists()


def test_find_native_schema_prefers_primary_discovery(monkeypatch) -> None:
    """Primary schema discovery wins when fallback has the same class name."""

    class PrimarySchema:
        pass

    class FallbackSchema:
        pass

    cli_schema_utils = types.ModuleType("phlo_pandera.cli_schema_utils")
    cli_schema_utils.discover_pandera_schemas = lambda: {"RawContractDemo": PrimarySchema}
    monkeypatch.setitem(sys.modules, "phlo_pandera.cli_schema_utils", cli_schema_utils)
    monkeypatch.setattr(
        schema_migrate_commands,
        "_discover_pandera_schemas_from_files",
        lambda: {"RawContractDemo": FallbackSchema},
    )

    resolved = schema_migrate_commands._find_native_schema(
        table_name="raw.contract_demo",
        schema_class="RawContractDemo",
    )
    assert resolved is PrimarySchema


def test_discover_schema_for_table_uses_fallback_without_phlo_quality(monkeypatch) -> None:
    """Falls back to file discovery when phlo_quality discovery import is unavailable."""

    class RawContractDemo:
        pass

    real_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "phlo_pandera.cli_schema_utils":
            raise ImportError("phlo_pandera unavailable")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", fake_import)
    monkeypatch.setattr(
        schema_migrate_commands,
        "_discover_pandera_schemas_from_files",
        lambda: {"RawContractDemo": RawContractDemo},
    )

    resolved = schema_migrate_commands._discover_schema_for_table("raw.contract_demo")
    assert resolved is RawContractDemo


def test_collect_quality_checks_parses_contract_tags(monkeypatch) -> None:
    """Quality check payload includes parsed owner/consumers/sla from tags."""

    class FakeRegistry:
        def list_checks(self):
            class Check:
                asset_key = "dlt_contract_demo"
                name = "quality_contract_demo"
                severity = "error"
                blocking = True
                description = "quality checks"
                tags = {
                    "contract_owner": "platform-team",
                    "contract_consumers": "analytics,ml-pipeline",
                    "contract_sla": '{"quality_threshold": 0.99}',
                }

            return [Check()]

    monkeypatch.setattr(schema_migrate_commands, "get_capability_registry", lambda: FakeRegistry())
    checks = schema_migrate_commands._collect_quality_checks("raw.contract_demo")
    assert len(checks) == 1
    assert checks[0]["owner"] == "platform-team"
    assert checks[0]["consumers"] == ["analytics", "ml-pipeline"]
    assert checks[0]["sla"] == {"quality_threshold": 0.99}


def test_collect_contract_metadata_filters_matching_asset(monkeypatch) -> None:
    """Contract metadata should be sourced from the matching asset only."""

    class FakeRegistry:
        def list_assets(self):
            class OtherAsset:
                key = "dlt_other"
                metadata = {
                    "table_name": "warehouse.other",
                    "owner": "wrong-team",
                    "consumers": [{"name": "ignore"}],
                    "sla": {"quality_threshold": 0.5},
                }

            class MatchingAsset:
                key = "dlt_contract_demo"
                metadata = {
                    "table_name": "raw.contract_demo",
                    "owner": "platform-team",
                    "consumers": [
                        {"name": "analytics", "contact": "#analytics", "usage": None},
                        "ignore-me",
                    ],
                    "sla": {"quality_threshold": 0.99},
                }

            return [OtherAsset(), MatchingAsset()]

    monkeypatch.setattr(schema_migrate_commands, "get_capability_registry", lambda: FakeRegistry())

    metadata = schema_migrate_commands._collect_contract_metadata("raw.contract_demo")

    assert metadata["owner"] == "platform-team"
    assert metadata["consumers"] == [{"name": "analytics", "contact": "#analytics", "usage": None}]
    assert metadata["sla"] == {"quality_threshold": 0.99}


def test_collect_transform_refs_filters_and_deduplicates(monkeypatch) -> None:
    """Only dbt assets that depend on the target table should be returned."""

    class FakeRegistry:
        def list_assets(self):
            class MatchingByKey:
                key = "transform_a"
                kinds = {"dbt"}
                deps = ["dlt_contract_demo"]

            class MatchingByShortName:
                key = "transform_b"
                kinds = {"dbt"}
                deps = ["contract_demo"]

            class DuplicateMatch:
                key = "transform_a"
                kinds = {"dbt"}
                deps = ["dlt_contract_demo"]

            class NonDbt:
                key = "other"
                kinds = {"service"}
                deps = ["dlt_contract_demo"]

            class Irrelevant:
                key = "transform_c"
                kinds = {"dbt"}
                deps = ["dlt_other"]

            return [
                MatchingByKey(),
                MatchingByShortName(),
                DuplicateMatch(),
                NonDbt(),
                Irrelevant(),
            ]

    monkeypatch.setattr(schema_migrate_commands, "get_capability_registry", lambda: FakeRegistry())

    refs = schema_migrate_commands._collect_transform_refs("raw.contract_demo")

    assert refs == ["transform_a", "transform_b"]


def test_build_scaffold_payload_from_contract_rejects_table_mismatch(monkeypatch) -> None:
    """A contract file whose table name does not match the request should fail."""

    monkeypatch.setattr(
        schema_migrate_commands.schema_migrate_contracts,
        "read_contract",
        lambda path: {
            "table_name": "warehouse.other",
            "normalized_schema": {"fields": [], "metadata": {}},
        },
    )

    with pytest.raises(ValueError, match="Contract table mismatch"):
        schema_migrate_commands._build_scaffold_payload_from_contract(
            table_name="warehouse.customers",
            contract_path=Path(".phlo/contracts/warehouse__customers.json"),
        )
