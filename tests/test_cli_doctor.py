from click.testing import CliRunner

from phlo.cli.commands.doctor import DiagnosticResult, DiagnosticStatus, doctor_cmd


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
