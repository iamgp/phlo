"""Tests for `phlo materialize` CLI command behavior."""

from subprocess import PIPE, STDOUT
from unittest.mock import patch

from click.testing import CliRunner

from phlo_dagster.cli_materialize import materialize, wait_for_dagster_runtime


def test_materialize_help_is_user_facing() -> None:
    result = CliRunner().invoke(materialize, ["--help"])

    assert result.exit_code == 0
    assert "Materialize Dagster assets via Docker." in result.output
    assert "Args:" not in result.output
    assert "Returns:" not in result.output
    assert "Raises:" not in result.output


def test_wait_for_dagster_runtime_uses_ready_marker(monkeypatch) -> None:
    calls = []

    def fake_run(cmd, check, capture_output, text):
        calls.append(cmd)

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr("phlo_dagster.cli_materialize.subprocess.run", fake_run)

    wait_for_dagster_runtime("dagster-1", timeout_seconds=0.1)

    assert calls == [
        [
            "docker",
            "exec",
            "dagster-1",
            "sh",
            "-lc",
            "test -f /tmp/phlo-dagster-ready "
            "|| python -c 'import phlo_dagster.framework.definitions'",
        ]
    ]


def test_wait_for_dagster_runtime_times_out(monkeypatch) -> None:
    def fake_run(cmd, check, capture_output, text):
        class Result:
            returncode = 1

        return Result()

    monkeypatch.setattr("phlo_dagster.cli_materialize.subprocess.run", fake_run)
    monkeypatch.setattr("phlo_dagster.cli_materialize.time.sleep", lambda seconds: None)

    try:
        wait_for_dagster_runtime("dagster-1", timeout_seconds=0)
    except RuntimeError as exc:
        assert "still finishing runtime setup" in str(exc)
        assert "phlo services logs --tail 120 dagster" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


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


@patch(
    "phlo_dagster.cli_materialize.find_dagster_container",
    side_effect=AssertionError("dry-run should not inspect Docker"),
)
@patch("phlo_dagster.cli_materialize.get_project_name", return_value="mock-project")
def test_materialize_accepts_select_without_asset_argument(mock_project, mock_container) -> None:
    """Docs use `phlo materialize --select ...`; keep that path runnable."""
    runner = CliRunner()
    result = runner.invoke(materialize, ["--select", "tag:bronze", "--dry-run"])

    assert result.exit_code == 0
    assert "PHLO_CONTRACT_REFRESH_SELECTION=tag:bronze" in result.output
    assert "--select tag:bronze" in result.output


@patch("phlo_dagster.cli_materialize.find_dagster_container", return_value="mock-container")
@patch("phlo_dagster.cli_materialize.get_project_name", return_value="mock-project")
def test_materialize_failure_hides_raw_process_output(
    mock_project, mock_container, monkeypatch
) -> None:
    """Container stdout should go to structured debug logs, not normal CLI output."""

    class FakeStdout:
        def __iter__(self):
            return iter(['{"event":"internal"}\n', "User-facing failure\n"])

    class FakeProcess:
        stdout = FakeStdout()

        def wait(self) -> int:
            return 2

    def fake_popen(cmd, stdout, stderr, text):
        assert stdout is PIPE
        assert stderr is STDOUT
        assert text is True
        return FakeProcess()

    monkeypatch.setattr("phlo_dagster.cli_materialize.subprocess.Popen", fake_popen)
    monkeypatch.setattr("phlo_dagster.cli_materialize.wait_for_dagster_runtime", lambda _: None)

    result = CliRunner().invoke(materialize, ["dlt_orders"])

    assert result.exit_code != 0
    assert '{"event":"internal"}' not in result.output
    assert "Error: materialization failed" in result.output
    assert "Exit code: 2" in result.output
    assert "Last output: User-facing failure" in result.output
    assert "Run: phlo logs --level ERROR --limit 20" in result.output


@patch(
    "phlo_dagster.cli_materialize.find_dagster_container",
    side_effect=RuntimeError("Could not find running dagster container"),
)
@patch("phlo_dagster.cli_materialize.get_project_name", return_value="mock-project")
def test_materialize_missing_dagster_container_is_actionable(mock_project, mock_container) -> None:
    runner = CliRunner()

    result = runner.invoke(materialize, ["dlt_orders"])

    assert result.exit_code != 0
    assert "Traceback" not in result.output
    assert "Error: dagster is not available" in result.output
    assert "Make sure the dagster service is running." in result.output
    assert "Run: phlo services start" in result.output
