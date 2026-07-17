"""Focused tests for the release artifact golden-path harness."""

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "release_golden_path", REPO_ROOT / "scripts" / "release_golden_path.py"
)
assert _spec and _spec.loader
release_golden_path = importlib.util.module_from_spec(_spec)
sys.modules["release_golden_path"] = release_golden_path
_spec.loader.exec_module(release_golden_path)


def _config(tmp_path: Path) -> release_golden_path.RunConfig:
    project = tmp_path / "project"
    return release_golden_path.RunConfig(
        repo_root=tmp_path,
        project_dir=project,
        wheelhouse=tmp_path / "wheelhouse",
        operator_env=tmp_path / "operator-env",
        project_name="phlo-qa001-test",
    )


def test_compose_commands_are_project_scoped(tmp_path: Path) -> None:
    config = _config(tmp_path)

    assert release_golden_path.compose_command(config, "up", "--detach") == [
        "docker",
        "compose",
        "-p",
        "phlo-qa001-test",
        "--file",
        str(config.compose_file),
        "--env-file",
        str(config.project_dir / ".phlo" / ".env"),
        "--env-file",
        str(config.project_dir / ".phlo" / ".env.local"),
        "up",
        "--detach",
    ]


def test_project_names_are_unique() -> None:
    first = release_golden_path.project_name()
    second = release_golden_path.project_name()

    assert first.startswith("phlo-qa001-")
    assert second.startswith("phlo-qa001-")
    assert first != second


def test_virtualenv_executables_use_windows_scripts_directory(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path)
    operator_scripts = config.operator_env / "Scripts"
    project_scripts = config.project_env / "Scripts"
    operator_scripts.mkdir(parents=True)
    project_scripts.mkdir(parents=True)
    operator_python = operator_scripts / "python.exe"
    operator_bin = operator_scripts / "phlo.exe"
    project_python = project_scripts / "python.exe"
    for executable in (operator_python, operator_bin, project_python):
        executable.touch()

    monkeypatch.setattr(release_golden_path.os, "name", "nt")

    assert config.operator_python == operator_python
    assert config.operator_bin == operator_bin
    assert config.project_python == project_python


def test_virtualenv_executables_use_unix_bin_directory(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path)
    operator_bin = config.operator_env / "bin" / "phlo"
    project_python = config.project_env / "bin" / "python"
    operator_bin.parent.mkdir(parents=True)
    project_python.parent.mkdir(parents=True)
    operator_bin.touch()
    project_python.touch()

    monkeypatch.setattr(release_golden_path.os, "name", "posix")

    assert config.operator_bin == operator_bin
    assert config.project_python == project_python


def test_operator_install_uses_wheelhouse_and_not_editable_source(
    tmp_path: Path, monkeypatch
) -> None:
    config = _config(tmp_path)
    commands: list[list[str]] = []
    monkeypatch.setattr(release_golden_path, "run", lambda args, **_: commands.append(args))

    release_golden_path.install_operator(config)

    assert any(command[0:3] == ["uv", "pip", "install"] for command in commands)
    local_install = commands[-1]
    assert "--no-index" in local_install
    assert "--no-deps" in local_install
    assert "--reinstall" in local_install
    assert "--find-links" in local_install
    assert str(config.wheelhouse) in local_install
    assert "-e" not in local_install
    assert "." not in local_install
    assert local_install[-3:] == ["phlo", "phlo-dlt", "phlo-pandera"]
    assert "phlo[core-services]" in commands[-2]


def test_existing_project_or_sibling_is_rejected_without_touching_it(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        release_golden_path, "build_wheelhouse", lambda _: (_ for _ in ()).throw(AssertionError)
    )
    for existing_name in ("project", "wheelhouse", "operator-env"):
        case = tmp_path / existing_name
        project = case / "project"
        existing = project if existing_name == "project" else case / existing_name
        existing.mkdir(parents=True)
        marker = existing / "keep.txt"
        marker.write_text("caller-owned\n", encoding="utf-8")

        assert (
            release_golden_path.main(["--repo-root", str(case), "--project-dir", str(project)]) == 2
        )
        assert marker.read_text(encoding="utf-8") == "caller-owned\n"


def test_verify_rows_requires_a_positive_count(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path)
    result = release_golden_path.subprocess.CompletedProcess([], 0, stdout='"2"\n', stderr="")
    monkeypatch.setattr(release_golden_path, "run", lambda *args, **kwargs: result)

    release_golden_path.verify_rows(config)

    for output, expected in (
        ("\n", "no row count"),
        ("0\n", "no rows"),
        ("oops\n", "no row count"),
    ):
        invalid = release_golden_path.subprocess.CompletedProcess([], 0, stdout=output, stderr="")
        monkeypatch.setattr(
            release_golden_path, "run", lambda *args, result=invalid, **kwargs: result
        )
        try:
            release_golden_path.verify_rows(config)
        except RuntimeError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError(f"invalid raw.events result should fail: {output!r}")


def test_start_stack_diagnoses_owned_compose_failure_in_order(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path)
    commands: list[list[str]] = []
    startup_error = release_golden_path.subprocess.CalledProcessError(1, ["docker", "compose"])

    def fake_run(args, **kwargs):
        commands.append(args)
        if args[-3:] == ["up", "--detach", "--build"]:
            raise startup_error
        return release_golden_path.subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(release_golden_path, "run", fake_run)

    try:
        release_golden_path.start_stack(config)
    except release_golden_path.subprocess.CalledProcessError as exc:
        assert exc is startup_error
    else:
        raise AssertionError("startup failure should be re-raised")

    assert commands == [
        release_golden_path.compose_command(config, "up", "--detach", "--build"),
        release_golden_path.compose_command(config, "ps"),
        release_golden_path.compose_command(config, "logs", "--no-color", "--timestamps"),
    ]


def test_start_stack_diagnostics_do_not_mask_startup_failure(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path)
    startup_error = release_golden_path.subprocess.CalledProcessError(1, ["docker", "compose"])

    def fail_commands(args, **kwargs):
        if args[-3:] == ["up", "--detach", "--build"]:
            raise startup_error
        raise RuntimeError("diagnostic failed")

    monkeypatch.setattr(release_golden_path, "run", fail_commands)

    try:
        release_golden_path.start_stack(config)
    except release_golden_path.subprocess.CalledProcessError as exc:
        assert exc is startup_error
    else:
        raise AssertionError("startup failure should be re-raised")


def test_align_project_name_binds_cli_lookup_to_owned_compose_project(tmp_path: Path) -> None:
    config = _config(tmp_path)
    config.project_dir.mkdir()
    (config.project_dir / "phlo.yaml").write_text("name: csv-batch\ndescription: demo\n")

    release_golden_path.align_project_name(config)

    assert (config.project_dir / "phlo.yaml").read_text().splitlines()[0] == (
        "name: phlo-qa001-test"
    )


def test_cleanup_only_tears_down_owned_compose_project(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path)
    config.compose_file.parent.mkdir(parents=True)
    config.compose_file.write_text("services: {}\n", encoding="utf-8")
    commands: list[list[str]] = []
    monkeypatch.setattr(release_golden_path, "run", lambda args, **_: commands.append(args))

    errors = release_golden_path.cleanup(config, owned_paths={config.project_dir})

    assert errors == []
    assert commands == [
        release_golden_path.compose_command(config, "down", "--volumes", "--remove-orphans")
    ]
    assert not config.project_dir.exists()


def test_cleanup_removes_owned_paths_when_compose_down_fails(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path)
    config.compose_file.parent.mkdir(parents=True)
    config.compose_file.write_text("services: {}\n", encoding="utf-8")
    wheelhouse = tmp_path / "wheelhouse"
    operator_env = tmp_path / "operator-env"
    wheelhouse.mkdir()
    operator_env.mkdir()
    monkeypatch.setattr(
        release_golden_path,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("down failed")),
    )

    errors = release_golden_path.cleanup(
        config,
        owned_paths={config.project_dir, wheelhouse, operator_env},
    )

    assert [str(error) for error in errors] == ["down failed"]
    assert not config.project_dir.exists()
    assert not wheelhouse.exists()
    assert not operator_env.exists()


def test_runtime_error_returns_nonzero_without_masking_cleanup_failure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project = tmp_path / "project"

    def fail_validation(config: release_golden_path.RunConfig) -> None:
        config.project_dir.mkdir()
        config.compose_file.parent.mkdir()
        config.compose_file.write_text("services: {}\n", encoding="utf-8")
        raise RuntimeError("validation failed")

    monkeypatch.setattr(release_golden_path, "build_wheelhouse", fail_validation)
    monkeypatch.setattr(
        release_golden_path,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("down failed")),
    )

    result = release_golden_path.main(["--repo-root", str(tmp_path), "--project-dir", str(project)])

    assert result == 1
    assert not project.exists()
    stderr = capsys.readouterr().err
    assert "release golden path failed: validation failed" in stderr
    assert "release golden path cleanup failed: down failed" in stderr


def test_unexpected_exception_still_cleans_owned_paths(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"

    def fail_unexpectedly(config: release_golden_path.RunConfig) -> None:
        config.project_dir.mkdir()
        raise ValueError("unexpected validation error")

    monkeypatch.setattr(release_golden_path, "build_wheelhouse", fail_unexpectedly)

    result = release_golden_path.main(["--repo-root", str(tmp_path), "--project-dir", str(project)])

    assert result == 1
    assert not project.exists()


def test_dagster_build_receives_a_local_wheelhouse_arg() -> None:
    service = (REPO_ROOT / "packages/phlo-dagster/src/phlo_dagster/service.yaml").read_text()
    daemon = (REPO_ROOT / "packages/phlo-dagster/src/phlo_dagster/dagster-daemon.yaml").read_text()
    dockerfile = (REPO_ROOT / "packages/phlo-dagster/src/phlo_dagster/Dockerfile").read_text()
    trino_service = (REPO_ROOT / "packages/phlo-trino/src/phlo_trino/service.yaml").read_text()

    assert "PHLO_WHEELHOUSE: ${PHLO_WHEELHOUSE:-}" in service
    assert "PHLO_WHEELHOUSE: ${PHLO_WHEELHOUSE:-}" in daemon
    assert 'ARG PHLO_WHEELHOUSE=""' in dockerfile
    assert "FROM python:3.12-slim AS phlo-build-context" in dockerfile
    assert "COPY . ." in dockerfile
    assert "RUN mkdir -p /opt/phlo-build-context/wheelhouse" in dockerfile
    assert (
        "COPY --from=phlo-build-context /opt/phlo-build-context/wheelhouse /opt/phlo-wheelhouse"
        in dockerfile
    )
    assert "RUN --mount=" not in dockerfile
    assert "--no-index --no-deps --reinstall --find-links" in dockerfile
    assert '"phlo==$PHLO_VERSION"' in dockerfile
    local_reinstall = dockerfile.rindex(
        "uv pip install --system --no-index --no-deps --reinstall --find-links"
    )
    dependency_install = dockerfile.index(
        "uv pip install --system --prerelease explicit --find-links"
    )
    assert local_reinstall > dependency_install
    assert "- source: jvm.config" in trino_service
    assert "dest: trino/jvm.config" in trino_service


def test_configure_non_dev_compose_uses_docker_ephemeral_ports(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path)
    config.project_dir.mkdir()
    config.project_dir.joinpath(".phlo").mkdir()
    config.project_dir.joinpath(".phlo/.env.local").write_text("", encoding="utf-8")
    config.wheelhouse.mkdir()
    config.wheelhouse.joinpath("phlo.whl").write_text("wheel", encoding="utf-8")
    config.repo_root.joinpath("pyproject.toml").write_text(
        "[project]\nversion = '1.2.3'\n", encoding="utf-8"
    )
    monkeypatch.setattr(release_golden_path, "run", lambda *args, **kwargs: None)

    release_golden_path.configure_non_dev_compose(config)

    env_local = config.project_dir.joinpath(".phlo/.env.local").read_text()
    assert all(f"{name}=0\n" in env_local for name in release_golden_path.PORT_NAMES)
