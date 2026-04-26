from subprocess import CompletedProcess

from click.testing import CliRunner

from phlo.cli.commands.doctor import DiagnosticResult, DiagnosticStatus, doctor_cmd, run_diagnostics
from phlo.cli.main import cli


def test_diagnostic_result_serializes_to_json_payload() -> None:
    result = DiagnosticResult(
        id="env.docker",
        group="Environment",
        status=DiagnosticStatus.FAIL,
        message="Docker daemon is not reachable",
        fix="Start Docker Desktop, then run phlo doctor again.",
        details={"returncode": 1},
    )

    assert result.to_payload() == {
        "id": "env.docker",
        "group": "Environment",
        "status": "fail",
        "message": "Docker daemon is not reachable",
        "fix": "Start Docker Desktop, then run phlo doctor again.",
        "details": {"returncode": 1},
    }


def test_doctor_json_outputs_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        "phlo.cli.commands.doctor.run_diagnostics",
        lambda verbose=False: [
            DiagnosticResult("env.python", "Environment", DiagnosticStatus.OK, "Python 3.13.5"),
            DiagnosticResult("env.docker", "Environment", DiagnosticStatus.FAIL, "Docker missing"),
        ],
    )

    result = CliRunner().invoke(doctor_cmd, ["--json"])

    assert result.exit_code == 1
    assert '"ok": 1' in result.output
    assert '"fail": 1' in result.output
    assert '"env.docker"' in result.output


def test_doctor_is_registered_on_root_cli() -> None:
    result = CliRunner().invoke(cli, ["doctor", "--json"])

    assert result.exit_code == 0
    assert '"doctor.bootstrap"' in result.output


def test_environment_checks_report_missing_docker(monkeypatch) -> None:
    monkeypatch.setattr(
        "phlo.cli.commands.doctor.shutil.which",
        lambda name: None if name == "docker" else f"/usr/bin/{name}",
    )
    monkeypatch.setattr(
        "phlo.cli.commands.doctor._run_probe",
        lambda command: CompletedProcess(command, 0, "Docker Compose version v2.0.0", ""),
    )
    monkeypatch.setattr("phlo.cli.commands.doctor.shutil.disk_usage", lambda path: (100, 50, 50))

    results = [result for result in run_diagnostics() if result.group == "Environment"]

    assert any(
        result.id == "env.docker.cli" and result.status == DiagnosticStatus.FAIL
        for result in results
    )
    assert any(result.id == "env.uv" and result.status == DiagnosticStatus.OK for result in results)


def test_environment_checks_report_compose_failure(monkeypatch) -> None:
    monkeypatch.setattr("phlo.cli.commands.doctor.shutil.which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        "phlo.cli.commands.doctor._run_probe",
        lambda command: CompletedProcess(command, 1, "", "compose missing"),
    )
    monkeypatch.setattr("phlo.cli.commands.doctor.shutil.disk_usage", lambda path: (100, 50, 50))

    results = run_diagnostics()

    assert any(
        result.id == "env.docker.compose" and result.status == DiagnosticStatus.FAIL
        for result in results
    )
