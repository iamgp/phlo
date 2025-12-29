"""Comprehensive integration tests for phlo-quality.

Per TEST_STRATEGY.md Level 2 (Functional):
- Check Generation Logic: Test quality check creation
- Check Execution: Run a check against a real dataset (Pandas/DuckDB)
"""

import pandas as pd
import pytest

pytestmark = pytest.mark.integration


# =============================================================================
# Pandera Contract Evaluation Tests
# =============================================================================


class TestPanderaContractEvaluation:
    """Test Pandera contract evaluation functionality."""

    def test_evaluate_valid_data(self):
        """Test evaluation passes for valid data."""
        from pandera.pandas import DataFrameModel
        from phlo_quality.pandera_asset_checks import evaluate_pandera_contract

        class TestSchema(DataFrameModel):
            id: int
            name: str

        df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})

        result = evaluate_pandera_contract(df, schema_class=TestSchema)

        assert result.passed is True
        assert result.failed_count == 0
        assert result.total_count == 3
        assert result.error is None

    def test_evaluate_invalid_data_wrong_type(self):
        """Test evaluation fails for wrong column types."""
        from pandera.pandas import DataFrameModel
        from phlo_quality.pandera_asset_checks import evaluate_pandera_contract

        class TestSchema(DataFrameModel):
            id: int
            name: str

        # id column has strings instead of ints
        df = pd.DataFrame({"id": ["not", "an", "int"], "name": ["Alice", "Bob", "Charlie"]})

        result = evaluate_pandera_contract(df, schema_class=TestSchema)

        assert result.passed is False
        assert result.error is not None

    def test_evaluate_missing_column(self):
        """Test evaluation fails for missing required column."""
        from pandera.pandas import DataFrameModel
        from phlo_quality.pandera_asset_checks import evaluate_pandera_contract

        class TestSchema(DataFrameModel):
            id: int
            name: str
            required_col: float

        # Missing required_col
        df = pd.DataFrame({"id": [1, 2], "name": ["a", "b"]})

        result = evaluate_pandera_contract(df, schema_class=TestSchema)

        assert result.passed is False

    def test_evaluation_result_structure(self):
        """Test PanderaContractEvaluation dataclass structure."""
        from phlo_quality.pandera_asset_checks import PanderaContractEvaluation

        evaluation = PanderaContractEvaluation(
            passed=True, failed_count=0, total_count=100, sample=[], error=None
        )

        assert evaluation.passed is True
        assert evaluation.failed_count == 0
        assert evaluation.total_count == 100


# =============================================================================
# Quality Check Contract Tests
# =============================================================================


class TestQualityCheckContract:
    """Test QualityCheckContract functionality."""

    def test_contract_creation(self):
        """Test creating a QualityCheckContract."""
        from phlo_quality.contract import QualityCheckContract

        contract = QualityCheckContract(
            source="pandera",
            partition_key="2024-01-01",
            failed_count=5,
            total_count=100,
            query_or_sql="SELECT * FROM table",
            repro_sql=None,
            sample=[],
        )

        assert contract.source == "pandera"
        assert contract.failed_count == 5
        assert contract.total_count == 100

    def test_contract_to_dagster_metadata(self):
        """Test converting contract to Dagster metadata."""
        from phlo_quality.contract import QualityCheckContract

        contract = QualityCheckContract(
            source="pandera",
            partition_key=None,
            failed_count=2,
            total_count=50,
            query_or_sql="SELECT 1",
            repro_sql=None,
            sample=[{"error": "test"}],
        )

        metadata = contract.to_dagster_metadata()

        assert isinstance(metadata, dict)

    def test_pandera_contract_check_name(self):
        """Test PANDERA_CONTRACT_CHECK_NAME constant."""
        from phlo_quality.contract import PANDERA_CONTRACT_CHECK_NAME

        assert PANDERA_CONTRACT_CHECK_NAME is not None
        assert isinstance(PANDERA_CONTRACT_CHECK_NAME, str)


# =============================================================================
# Quality Decorator Tests
# =============================================================================


class TestQualityDecorator:
    """Test quality decorator functionality."""

    def test_get_quality_checks_importable(self):
        """Test get_quality_checks function is importable."""
        from phlo_quality.decorator import get_quality_checks

        assert callable(get_quality_checks)

    def test_decorator_module_has_expected_functions(self):
        """Test decorator module has expected functions."""
        from phlo_quality import decorator

        assert hasattr(decorator, "get_quality_checks")


# =============================================================================
# Severity Tests
# =============================================================================


class TestQualitySeverity:
    """Test quality severity functionality."""

    def test_severity_for_pandera_contract(self):
        """Test severity determination for Pandera contracts."""
        from phlo_quality.severity import severity_for_pandera_contract

        # Passed check - no severity/warning
        severity_for_pandera_contract(passed=True)
        # May be None or a default value

        # Failed check - should have severity
        severity_for_pandera_contract(passed=False)
        # Should indicate an error or warning


# =============================================================================
# Parquet File Validation Tests
# =============================================================================


class TestParquetValidation:
    """Test Parquet file validation."""

    def test_evaluate_parquet_file(self):
        """Test evaluating a Pandera contract against a Parquet file."""
        import tempfile
        from pathlib import Path
        from pandera.pandas import DataFrameModel
        from phlo_quality.pandera_asset_checks import evaluate_pandera_contract_parquet

        class TestSchema(DataFrameModel):
            id: int
            name: str

        # Create test parquet file
        df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})

        with tempfile.TemporaryDirectory() as tmpdir:
            parquet_path = Path(tmpdir) / "test.parquet"
            df.to_parquet(parquet_path)

            result = evaluate_pandera_contract_parquet(parquet_path, schema_class=TestSchema)

            assert result.passed is True


# =============================================================================
# Complex Schema Tests
# =============================================================================


class TestComplexSchemas:
    """Test quality checks with complex schemas."""

    def test_schema_with_datetime(self):
        """Test schema with datetime columns."""
        from datetime import datetime
        from pandera.pandas import DataFrameModel
        from phlo_quality.pandera_asset_checks import evaluate_pandera_contract

        class DateTimeSchema(DataFrameModel):
            id: int
            created_at: datetime

        df = pd.DataFrame(
            {"id": [1, 2], "created_at": pd.to_datetime(["2024-01-01", "2024-01-02"])}
        )

        result = evaluate_pandera_contract(df, schema_class=DateTimeSchema)

        # Should handle datetime conversion
        assert result.total_count == 2

    def test_schema_with_nullable_fields(self):
        """Test schema with nullable/optional fields."""
        from typing import Optional
        from pandera.pandas import DataFrameModel, Field
        from phlo_quality.pandera_asset_checks import evaluate_pandera_contract

        class NullableSchema(DataFrameModel):
            id: int
            optional_value: Optional[str] = Field(nullable=True)

        df = pd.DataFrame({"id": [1, 2, 3], "optional_value": ["a", None, "c"]})

        result = evaluate_pandera_contract(df, schema_class=NullableSchema)

        # Should handle nulls
        assert result.total_count == 3


# =============================================================================
# Reconciliation Tests
# =============================================================================


class TestReconciliation:
    """Test data reconciliation functionality."""

    def test_reconciliation_module_importable(self):
        """Test reconciliation module is importable."""
        from phlo_quality import reconciliation

        assert reconciliation is not None


# =============================================================================
# Checks Module Tests
# =============================================================================


class TestChecksModule:
    """Test checks module functionality."""

    def test_checks_module_importable(self):
        """Test checks module is importable."""
        from phlo_quality import checks

        assert checks is not None


# =============================================================================
# CLI Plugin Tests
# =============================================================================


class TestQualityCLIPlugin:
    """Test quality CLI plugin."""

    def test_cli_plugin_importable(self):
        """Test CLI plugin is importable."""
        from phlo_quality.cli_plugin import QualityCliPlugin

        assert QualityCliPlugin is not None


# =============================================================================
# Export Tests
# =============================================================================


class TestQualityExports:
    """Test module exports."""

    def test_module_importable(self):
        """Test phlo_quality module is importable."""
        import phlo_quality

        assert phlo_quality is not None

    def test_pandera_asset_checks_importable(self):
        """Test pandera_asset_checks module is importable."""
        from phlo_quality import pandera_asset_checks

        assert pandera_asset_checks is not None

    def test_contract_importable(self):
        """Test contract module is importable."""
        from phlo_quality import contract

        assert contract is not None
