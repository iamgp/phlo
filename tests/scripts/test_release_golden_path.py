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


def test_existing_project_dir_is_rejected_without_touching_it(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    project.mkdir()
    marker = project / "keep.txt"
    marker.write_text("caller-owned\n", encoding="utf-8")
    monkeypatch.setattr(
        release_golden_path, "build_wheelhouse", lambda _: (_ for _ in ()).throw(AssertionError)
    )

    assert (
        release_golden_path.main(["--repo-root", str(tmp_path), "--project-dir", str(project)]) == 2
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


def test_align_project_name_binds_cli_lookup_to_owned_compose_project(tmp_path: Path) -> None:
    config = _config(tmp_path)
    config.project_dir.mkdir()
    (config.project_dir / "phlo.yaml").write_text("name: csv-batch\ndescription: demo\n")

    release_golden_path.align_project_name(config)

    assert (config.project_dir / "phlo.yaml").read_text().splitlines()[0] == (
        "name: phlo-qa001-test"
    )


def test_cleanup_only_targets_owned_compose_project(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path)
    config.compose_file.parent.mkdir(parents=True)
    config.compose_file.write_text("services: {}\n", encoding="utf-8")
    commands: list[list[str]] = []
    monkeypatch.setattr(release_golden_path, "run", lambda args, **_: commands.append(args))

    release_golden_path.cleanup(config, owned_paths={config.project_dir})

    assert commands == [
        release_golden_path.compose_command(config, "down", "--volumes", "--remove-orphans")
    ]
    assert not config.project_dir.exists()


def test_dagster_build_receives_a_local_wheelhouse_arg() -> None:
    service = Path("packages/phlo-dagster/src/phlo_dagster/service.yaml").read_text()
    daemon = Path("packages/phlo-dagster/src/phlo_dagster/dagster-daemon.yaml").read_text()
    dockerfile = Path("packages/phlo-dagster/src/phlo_dagster/Dockerfile").read_text()
    trino_service = Path("packages/phlo-trino/src/phlo_trino/service.yaml").read_text()

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


def test_find_free_port_skips_reserved_ports(tmp_path: Path) -> None:
    del tmp_path
    reserved = {20000}

    port = release_golden_path.find_free_port(start=20000, reserved=reserved)

    assert port != 20000
    assert port in reserved
