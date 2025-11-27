"""
Tests for spec 010: Data Contracts & Schema Evolution.

Tests cover:
- Contract definition and loading
- Schema evolution analysis
- Breaking change detection
- SLA validation
- Notification system
"""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from phlo.cli.main import cli
from phlo.contracts.schema import (
    Contract,
    ContractRegistry,
    ContractValidator,
    ColumnDefinition,
    SLAConfig,
)
from phlo.contracts.evolution import SchemaEvolution, ChangeClassification, FieldChange
from phlo.contracts.notifications import (
    NotificationManager,
    ContractNotification,
    NotificationType,
    NotificationChannel,
)


class TestContractDefinition:
    """Test contract loading and validation."""

    def test_contract_from_yaml(self):
        """Test loading contract from YAML."""
        yaml_content = """
name: test_contract
version: 1.0.0
owner: test-team
description: Test contract
schema:
  required_columns:
    - name: id
      type: string
      required: true
    - name: value
      type: integer
      required: true
sla:
  freshness_hours: 24
  quality_threshold: 0.99
consumers:
  - name: team-a
    usage: analytics
"""
        contract = Contract.from_yaml(yaml_content)

        assert contract.name == "test_contract"
        assert contract.version == "1.0.0"
        assert contract.owner == "test-team"
        assert len(contract.schema_columns) == 2
        assert contract.sla.freshness_hours == 24
        assert len(contract.consumers) == 1

    def test_contract_to_dict(self):
        """Test converting contract to dictionary."""
        col = ColumnDefinition(name="id", type="string", required=True)
        contract = Contract(
            name="test",
            version="1.0.0",
            owner="owner",
            schema_columns=[col],
        )

        data = contract.to_dict()

        assert data["name"] == "test"
        assert data["version"] == "1.0.0"
        assert len(data["schema"]["required_columns"]) == 1

    def test_contract_registry_load(self):
        """Test loading contracts from directory."""
        registry = ContractRegistry(Path("examples/glucose-platform/contracts"))

        # Should find example contracts
        contracts = registry.list_contracts()
        assert len(contracts) > 0
        assert "glucose_readings" in contracts
        assert "customer_data" in contracts

    def test_contract_registry_get(self):
        """Test retrieving contract from registry."""
        registry = ContractRegistry(Path("examples/glucose-platform/contracts"))
        contract = registry.get("glucose_readings")

        assert contract is not None
        assert contract.name == "glucose_readings"
        assert contract.owner == "data-team"


class TestContractValidator:
    """Test schema validation against contracts."""

    def test_validate_valid_schema(self):
        """Test validating conforming schema."""
        col = ColumnDefinition(name="id", type="string", required=True)
        contract = Contract(
            name="test",
            version="1.0.0",
            owner="owner",
            schema_columns=[col],
        )

        validator = ContractValidator(contract)
        actual_schema = {"id": "string"}

        valid, errors = validator.validate_schema(actual_schema)

        assert valid is True
        assert len(errors) == 0

    def test_validate_missing_column(self):
        """Test validation with missing required column."""
        col = ColumnDefinition(name="id", type="string", required=True)
        contract = Contract(
            name="test",
            version="1.0.0",
            owner="owner",
            schema_columns=[col],
        )

        validator = ContractValidator(contract)
        actual_schema = {}  # Missing 'id'

        valid, errors = validator.validate_schema(actual_schema)

        assert valid is False
        assert any("Missing" in error for error in errors)

    def test_validate_type_mismatch(self):
        """Test validation with type mismatch."""
        col = ColumnDefinition(name="id", type="string", required=True)
        contract = Contract(
            name="test",
            version="1.0.0",
            owner="owner",
            schema_columns=[col],
        )

        validator = ContractValidator(contract)
        actual_schema = {"id": "integer"}  # Wrong type

        valid, errors = validator.validate_schema(actual_schema)

        assert valid is False
        assert any("Column" in error or "id" in error for error in errors)

    def test_validate_sla_quality(self):
        """Test SLA quality validation."""
        contract = Contract(
            name="test",
            version="1.0.0",
            owner="owner",
            sla=SLAConfig(quality_threshold=0.99),
        )

        validator = ContractValidator(contract)

        # Pass SLA
        metrics = {"quality_score": 0.995}
        sla_met, violations = validator.validate_sla(metrics)
        assert sla_met is True

        # Fail SLA
        metrics = {"quality_score": 0.98}
        sla_met, violations = validator.validate_sla(metrics)
        assert sla_met is False
        assert any("Quality" in v for v in violations)

    def test_validate_sla_freshness(self):
        """Test SLA freshness validation."""
        contract = Contract(
            name="test",
            version="1.0.0",
            owner="owner",
            sla=SLAConfig(freshness_hours=24),
        )

        validator = ContractValidator(contract)

        # Fresh data
        metrics = {"freshness_hours": 12}
        sla_met, violations = validator.validate_sla(metrics)
        assert sla_met is True

        # Stale data
        metrics = {"freshness_hours": 48}
        sla_met, violations = validator.validate_sla(metrics)
        assert sla_met is False
        assert any("freshness" in v.lower() for v in violations)


class TestSchemaEvolution:
    """Test schema evolution analysis."""

    def test_added_optional_column_is_safe(self):
        """Test that adding optional column is safe."""
        old_cols = [ColumnDefinition(name="id", type="string", required=True)]
        new_cols = [
            ColumnDefinition(name="id", type="string", required=True),
            ColumnDefinition(name="description", type="string", required=False),
        ]

        analysis = SchemaEvolution.analyze(old_cols, new_cols)

        assert analysis.classification == ChangeClassification.SAFE

    def test_removed_column_is_breaking(self):
        """Test that removing column is breaking."""
        old_cols = [
            ColumnDefinition(name="id", type="string", required=True),
            ColumnDefinition(name="value", type="integer", required=True),
        ]
        new_cols = [ColumnDefinition(name="id", type="string", required=True)]

        analysis = SchemaEvolution.analyze(old_cols, new_cols)

        assert analysis.classification == ChangeClassification.BREAKING

    def test_type_change_is_breaking(self):
        """Test that changing column type is breaking."""
        old_cols = [ColumnDefinition(name="value", type="integer", required=True)]
        new_cols = [ColumnDefinition(name="value", type="string", required=True)]

        analysis = SchemaEvolution.analyze(old_cols, new_cols)

        assert analysis.classification == ChangeClassification.BREAKING

    def test_making_optional_required_is_breaking(self):
        """Test that making optional column required is breaking."""
        old_cols = [ColumnDefinition(name="value", type="string", required=False)]
        new_cols = [ColumnDefinition(name="value", type="string", required=True)]

        analysis = SchemaEvolution.analyze(old_cols, new_cols)

        assert analysis.classification == ChangeClassification.BREAKING

    def test_making_required_optional_is_safe(self):
        """Test that making required column optional is safe."""
        old_cols = [ColumnDefinition(name="value", type="string", required=True)]
        new_cols = [ColumnDefinition(name="value", type="string", required=False)]

        analysis = SchemaEvolution.analyze(old_cols, new_cols)

        assert analysis.classification == ChangeClassification.SAFE

    def test_backward_compatibility_check(self):
        """Test backward compatibility check."""
        old_cols = [ColumnDefinition(name="id", type="string", required=True)]
        new_cols = [
            ColumnDefinition(name="id", type="string", required=True),
            ColumnDefinition(name="new_field", type="string", required=False),
        ]

        compatible = SchemaEvolution.is_backward_compatible(old_cols, new_cols)

        assert compatible is True

    def test_get_breaking_changes(self):
        """Test extracting only breaking changes."""
        old_cols = [
            ColumnDefinition(name="id", type="string", required=True),
            ColumnDefinition(name="old_field", type="string", required=True),
        ]
        new_cols = [
            ColumnDefinition(name="id", type="string", required=True),
            ColumnDefinition(name="new_field", type="string", required=False),
        ]

        breaking = SchemaEvolution.get_breaking_changes(old_cols, new_cols)

        # Should find removed field as breaking
        assert any(c.change_type == "removed" for c in breaking)


class TestNotificationManager:
    """Test notification system."""

    def test_create_notification(self):
        """Test creating notifications."""
        notification = ContractNotification(
            type=NotificationType.SCHEMA_CHANGE_PROPOSED,
            contract_name="test",
            subject="Schema change",
            message="A new field was added",
        )

        assert notification.contract_name == "test"
        assert notification.type == NotificationType.SCHEMA_CHANGE_PROPOSED

    def test_notification_manager(self):
        """Test notification manager stores history."""
        manager = NotificationManager()

        notification = ContractNotification(
            type=NotificationType.SLA_BREACH,
            contract_name="test",
            subject="SLA violation",
            message="Quality threshold breached",
        )

        manager.notify(notification, channels=[])

        history = manager.get_notification_history()
        assert len(history) == 1
        assert history[0].contract_name == "test"

    def test_notification_filtering(self):
        """Test filtering notifications."""
        manager = NotificationManager()

        n1 = ContractNotification(
            type=NotificationType.SCHEMA_CHANGE_PROPOSED,
            contract_name="contract-a",
            subject="Change",
            message="Test",
        )
        n2 = ContractNotification(
            type=NotificationType.SLA_BREACH,
            contract_name="contract-b",
            subject="Breach",
            message="Test",
        )

        manager.notify(n1, channels=[])
        manager.notify(n2, channels=[])

        # Filter by contract
        results = manager.get_notification_history(contract_name="contract-a")
        assert len(results) == 1
        assert results[0].contract_name == "contract-a"

        # Filter by type
        results = manager.get_notification_history(
            notification_type=NotificationType.SLA_BREACH
        )
        assert len(results) == 1
        assert results[0].type == NotificationType.SLA_BREACH


class TestContractCLI:
    """Test contract CLI commands."""

    def test_contract_list(self):
        """Test phlo contract list command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["contract", "list", "--contracts-dir", "examples/glucose-platform/contracts"])

        assert result.exit_code == 0
        assert "glucose_readings" in result.output
        assert "customer_data" in result.output
        assert "Data Contracts" in result.output

    def test_contract_list_json(self):
        """Test phlo contract list with JSON output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["contract", "list", "--contracts-dir", "examples/glucose-platform/contracts", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "glucose_readings" in data
        assert "customer_data" in data

    def test_contract_show(self):
        """Test phlo contract show command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["contract", "show", "glucose_readings", "--contracts-dir", "examples/glucose-platform/contracts"])

        assert result.exit_code == 0
        assert "glucose_readings" in result.output
        assert "data-team" in result.output
        assert "SLA" in result.output

    def test_contract_show_not_found(self):
        """Test phlo contract show with invalid contract."""
        runner = CliRunner()
        result = runner.invoke(cli, ["contract", "show", "nonexistent", "--contracts-dir", "examples/glucose-platform/contracts"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_contract_validate(self):
        """Test phlo contract validate command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["contract", "validate", "glucose_readings", "--contracts-dir", "examples/glucose-platform/contracts"])

        assert result.exit_code == 0
        assert "glucose_readings" in result.output

    def test_contract_check(self):
        """Test phlo contract check command for breaking changes."""
        runner = CliRunner()
        result = runner.invoke(cli, ["contract", "check", "glucose_readings", "--contracts-dir", "examples/glucose-platform/contracts"])

        assert result.exit_code == 0
        assert "Analysis" in result.output or "Classification" in result.output

    def test_contract_check_json(self):
        """Test phlo contract check with JSON output."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["contract", "check", "glucose_readings", "--contracts-dir", "examples/glucose-platform/contracts", "--format", "json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "classification" in data
        assert "changes" in data
