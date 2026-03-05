"""Unit tests for the bundled-stack contract harness utilities."""

from __future__ import annotations

from pathlib import Path

from phlo_testing.profile_harness import (
    BUNDLED_STACK_DEV_PACKAGES,
    BundledStackHarness,
    BundledStackPorts,
    build_bundled_stack_env_updates,
    bundled_stack_contract_enabled,
)


def test_bundled_stack_contract_enabled_reads_truthy_env(
    monkeypatch,
) -> None:
    monkeypatch.setenv("PHLO_RUN_BUNDLED_STACK_CONTRACT", "true")
    assert bundled_stack_contract_enabled() is True


def test_build_bundled_stack_env_updates_resolves_core_ports() -> None:
    calls: list[tuple[str, int]] = []

    def fake_resolve_port(service_name: str, default_port: int) -> int:
        calls.append((service_name, default_port))
        return default_port + 10

    updates = build_bundled_stack_env_updates(fake_resolve_port)

    assert updates["DAGSTER_PORT"] == "3010"
    assert updates["POSTGRES_PORT"] == "5442"
    assert updates["PHLO_DEV_EXTRA_PACKAGES"] == ",".join(BUNDLED_STACK_DEV_PACKAGES)
    assert ("Dagster", 3000) in calls
    assert ("Nessie", 19120) in calls


def test_bundled_stack_harness_materialize_adds_partition(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_phlo(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return "ok"

    monkeypatch.setattr(
        "phlo_testing.profile_harness._load_golden_path_module",
        lambda: type(
            "StubGoldenPathModule",
            (),
            {"run_phlo": staticmethod(fake_run_phlo)},
        )(),
    )

    harness = BundledStackHarness(
        project_dir=Path("/tmp/project"),
        phlo_source=Path("/tmp/source"),
        python_executable=Path("/tmp/project/.venv/bin/python"),
        ports=BundledStackPorts(
            phlo_api=54000,
            dagster=3000,
            postgres=5432,
            trino=8080,
            minio_api=9000,
            minio_console=9001,
            nessie=19120,
        ),
    )

    result = harness.materialize("dlt_posts", partition_date="2025-01-01", stream_output=False)

    assert result == "ok"
    assert captured["args"] == ["materialize", "dlt_posts", "--partition", "2025-01-01"]
    assert captured["kwargs"] == {
        "cwd": Path("/tmp/project"),
        "timeout": 1200,
        "check": True,
        "stream_output": False,
        "python_exe": Path("/tmp/project/.venv/bin/python"),
    }
