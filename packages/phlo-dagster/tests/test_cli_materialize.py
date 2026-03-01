"""Tests for `phlo materialize` CLI command behavior."""

from unittest.mock import patch

from click.testing import CliRunner

from phlo_dagster.cli_materialize import materialize


@patch("phlo_dagster.cli_materialize.find_dagster_container", return_value="mock-container")
@patch("phlo_dagster.cli_materialize.get_project_name", return_value="mock-project")
def test_materialize_sets_contract_refresh_env_by_default(mock_project, mock_container) -> None:
    """Dry-run command enables contract refresh by default."""
    runner = CliRunner()
    result = runner.invoke(materialize, ["dlt_orders", "--dry-run"])

    assert result.exit_code == 0
    assert "PHLO_AUTO_REFRESH_CONTRACTS=1" in result.output
    assert "PHLO_CONTRACT_REFRESH_SELECTION=dlt_orders" in result.output


@patch("phlo_dagster.cli_materialize.find_dagster_container", return_value="mock-container")
@patch("phlo_dagster.cli_materialize.get_project_name", return_value="mock-project")
def test_materialize_can_disable_contract_refresh(mock_project, mock_container) -> None:
    """Dry-run command supports opt-out contract refresh flag."""
    runner = CliRunner()
    result = runner.invoke(
        materialize,
        ["dlt_orders", "--dry-run", "--no-contract-refresh"],
    )

    assert result.exit_code == 0
    assert "PHLO_AUTO_REFRESH_CONTRACTS=0" in result.output
