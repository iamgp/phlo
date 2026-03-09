"""Tests for Sling CLI commands."""

from __future__ import annotations

import json
import subprocess

from click.testing import CliRunner

from phlo_sling.cli_commands import discover_command, run_command


def test_run_command_derives_target_object_from_stream(monkeypatch) -> None:
    """Ad-hoc runs should pass a target object to Sling."""
    captured: dict[str, object] = {}

    class _FakeSling:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def run(self) -> None:
            captured["ran"] = True

    monkeypatch.setattr("phlo_sling.cli_commands.apply_sling_connection_env", lambda: {})
    monkeypatch.setattr("sling.Sling", _FakeSling)

    result = CliRunner().invoke(
        run_command,
        ["--source", "SRC", "--stream", "public.users", "--target", "TGT"],
    )

    assert result.exit_code == 0
    assert captured["src_conn"] == "SRC"
    assert captured["src_stream"] == "public.users"
    assert captured["tgt_conn"] == "TGT"
    assert captured["tgt_object"] == "public.users"
    assert captured["ran"] is True


def test_run_command_requires_object_for_wildcard_stream(monkeypatch) -> None:
    """Wildcard streams need an explicit target object in ad-hoc mode."""
    monkeypatch.setattr("phlo_sling.cli_commands.apply_sling_connection_env", lambda: {})

    result = CliRunner().invoke(
        run_command,
        ["--source", "SRC", "--stream", "public.*", "--target", "TGT"],
    )

    assert result.exit_code != 0
    assert "Provide --object when --stream uses a wildcard." in result.output


def test_discover_command_uses_sling_conns_discover(monkeypatch) -> None:
    """Discovery should shell out to Sling's connection introspection command."""
    calls: list[list[str]] = []

    def _run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout="Database | Schema | Table\n-------- | ------ | -----\nwarehouse | public | users\n",
            stderr="",
        )

    monkeypatch.setattr("phlo_sling.cli_commands.apply_sling_connection_env", lambda: {})
    monkeypatch.setattr("phlo_sling.cli_commands._run_sling_cli_command", _run_command)

    result = CliRunner().invoke(
        discover_command,
        ["PHLO_POSTGRES", "--schema", "public", "--format", "json"],
    )

    assert result.exit_code == 0
    assert calls == [["conns", "discover", "PHLO_POSTGRES", "--pattern", "public.*"]]
    _, json_output = result.output.split("\n", 1)
    payload = json.loads(json_output)
    assert payload == [{"database": "warehouse", "schema": "public", "table": "users"}]
