"""Integration tests for phlo-quality."""

import pytest

pytestmark = pytest.mark.integration


def test_pandera_checks_importable():
    """Test that Pandera checks are importable."""
    from phlo_quality.pandera_asset_checks import (
        evaluate_pandera_contract,
        PanderaContractEvaluation,
    )

    assert evaluate_pandera_contract is not None
    assert PanderaContractEvaluation is not None


def test_quality_contract_importable():
    """Test that QualityCheckContract is importable."""
    from phlo_quality.contract import QualityCheckContract, PANDERA_CONTRACT_CHECK_NAME

    assert QualityCheckContract is not None
    assert PANDERA_CONTRACT_CHECK_NAME is not None


def test_quality_check_evaluation():
    """Test quality check evaluation with sample data."""
    import pandas as pd
    from pandera.pandas import DataFrameModel
    from phlo_quality.pandera_asset_checks import evaluate_pandera_contract

    class TestSchema(DataFrameModel):
        id: int
        name: str

    # Valid data
    df = pd.DataFrame({"id": [1, 2], "name": ["a", "b"]})
    result = evaluate_pandera_contract(df, schema_class=TestSchema)
    assert result.passed is True


def test_quality_check_failure():
    """Test quality check detects invalid data."""
    import pandas as pd
    from pandera.pandas import DataFrameModel
    from phlo_quality.pandera_asset_checks import evaluate_pandera_contract

    class TestSchema(DataFrameModel):
        id: int
        name: str

    # Invalid data (missing column)
    df = pd.DataFrame({"id": [1, 2]})
    result = evaluate_pandera_contract(df, schema_class=TestSchema)
    assert result.passed is False


def test_quality_decorator_importable():
    """Test that quality decorator is importable."""
    from phlo_quality.decorator import get_quality_checks

    assert get_quality_checks is not None
