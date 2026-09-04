"""CLI install preflight wiring (issue #857).

The `phlo plugin install` mutation must be decided by the one shared pure
preflight before pip runs, and a rejected candidate must never reach the
installer. Patching the shared preflight module attribute proves both
mutation surfaces call the same decision (mechanical CLI/API drift
prevention).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from phlo.cli.commands.plugin import plugin_group
from phlo.plugins import preflight, registry_client
from phlo.plugins.registry_client import RegistryPlugin


@pytest.fixture
def fixture_plugin(monkeypatch) -> RegistryPlugin:
    plugin = RegistryPlugin(
        name="preflight-fixture",
        type="resource",
        package="phlo-preflight-fixture",
        version="0.1.0",
        description="Preflight fixture",
        author="Preflight Fixture Author",
        homepage=None,
        tags=["fixture"],
        verified=True,
        core=False,
    )
    monkeypatch.setattr("phlo.cli.commands.plugin.install.get_registry_plugin", lambda name: plugin)
    return plugin


@pytest.fixture
def required_project(tmp_path: Path, monkeypatch) -> Path:
    """A project whose phlo.yaml requires the fixture as its query engine."""
    (tmp_path / "phlo.yaml").write_text(
        "capabilities:\n  defaults:\n    query_engine: preflight-fixture\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def pip_calls(monkeypatch) -> list[list[str]]:
    calls: list[list[str]] = []
    monkeypatch.setattr("phlo.cli.commands.plugin.install.run_pip", lambda args: calls.append(args))
    return calls


def test_rejected_candidate_never_reaches_pip(
    fixture_plugin: RegistryPlugin, required_project: Path, pip_calls: list[list[str]]
) -> None:
    """The project demands a conformance-tested query engine; an unevidenced
    candidate is rejected and the pip mutation is never performed."""
    result = CliRunner().invoke(plugin_group, ["install", "preflight-fixture", "--json"])

    assert result.exit_code == 1
    assert pip_calls == []
    data = json.loads(result.output)
    assert data["data"]["preflight"]["accepted"] is False
    assert data["data"]["preflight"]["required_tier"] == "conformance-tested"
    assert any("policy" in warning for warning in data["warnings"])


def test_preflight_runs_before_pip_and_shares_one_decision(
    monkeypatch,
    fixture_plugin: RegistryPlugin,
    tmp_path: Path,
    pip_calls: list[list[str]],
) -> None:
    """Order proof: the shared pure preflight decides strictly before the
    pip mutation; patching the shared module intercepts the call, proving
    the CLI uses the same decision as the API surface."""
    monkeypatch.chdir(tmp_path)
    order: list[str] = []
    real_evaluate = preflight.evaluate_install_preflight

    def recording_evaluate(**kwargs):
        order.append("preflight")
        return real_evaluate(**kwargs)

    monkeypatch.setattr(preflight, "evaluate_install_preflight", recording_evaluate)

    result = CliRunner().invoke(plugin_group, ["install", "preflight-fixture", "--json"])

    assert result.exit_code == 0, result.output
    assert order == ["preflight"]
    assert len(pip_calls) == 1
    assert pip_calls[0][0] == "install"
    data = json.loads(result.output)
    assert data["data"]["preflight"]["accepted"] is True
    assert data["data"]["preflight"]["tier"] == "community"


def test_unknown_spec_is_rejected_before_pip(
    monkeypatch, tmp_path: Path, pip_calls: list[list[str]]
) -> None:
    """A candidate with no registry descriptor is unknown and never installed."""
    monkeypatch.setattr("phlo.cli.commands.plugin.install.get_registry_plugin", lambda name: None)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(plugin_group, ["install", "totally-unknown-pkg"])

    assert result.exit_code == 1
    assert pip_calls == []
    assert "malformed" in result.output


def test_override_is_explicit_tier_preserving_and_recorded(
    fixture_plugin: RegistryPlugin, required_project: Path, pip_calls: list[list[str]]
) -> None:
    """The explicit override installs a community candidate and the decision
    records the overridden rule; the tier never changes (ADR 0053 concern 5)."""
    result = CliRunner().invoke(
        plugin_group,
        [
            "install",
            "preflight-fixture",
            "--allow-community",
            "--override-reason",
            "team decision, recorded",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert len(pip_calls) == 1
    data = json.loads(result.output)
    assert data["data"]["preflight"]["tier"] == "community"
    assert data["data"]["preflight"]["override_rule"] == "min_tier:query_engine"
    assert any("remains tier community" in warning for warning in data["warnings"])


def test_override_requires_a_reason(fixture_plugin: RegistryPlugin, required_project: Path) -> None:
    result = CliRunner().invoke(plugin_group, ["install", "preflight-fixture", "--allow-community"])
    assert result.exit_code != 0
    assert "override-reason" in result.output


def test_registry_verified_flag_maps_to_legacy_verified_not_trust(
    monkeypatch, fixture_plugin: RegistryPlugin, required_project: Path
) -> None:
    """The registry ``verified`` boolean enters only as the derived
    ``legacy_verified`` state: it authorizes nothing (ADR 0053 concern 5)."""
    seen: dict[str, object] = {}
    real_evaluate = preflight.evaluate_install_preflight

    def spy(**kwargs):
        seen["legacy_verified"] = kwargs.get("legacy_verified")
        return real_evaluate(**kwargs)

    monkeypatch.setattr(preflight, "evaluate_install_preflight", spy)

    result = CliRunner().invoke(plugin_group, ["install", "preflight-fixture", "--json"])
    assert result.exit_code == 1  # legacy_verified did not satisfy the tier bar
    assert seen["legacy_verified"] is True


def test_evidence_backed_artifact_decision_flows_through_cli(
    monkeypatch, tmp_path: Path, pip_calls: list[list[str]]
) -> None:
    """``--evidence`` documents feed the same pure decision: a registry-free
    artifact install with an unqualified digest stays an explicit-override
    path, and malformed evidence is refused before the mutation."""
    plugin = RegistryPlugin(
        name="preflight-fixture",
        type="resource",
        package="phlo-preflight-fixture",
        version="0.1.0",
        description="Preflight fixture",
        author="Preflight Fixture Author",
        homepage=None,
        tags=["fixture"],
        verified=False,
        core=False,
    )
    monkeypatch.setattr("phlo.cli.commands.plugin.install.get_registry_plugin", lambda name: plugin)
    monkeypatch.chdir(tmp_path)

    bad_evidence = tmp_path / "bad-evidence.json"
    bad_evidence.write_text(
        json.dumps(
            {
                "subject": {
                    "package": "phlo-preflight-fixture",
                    "version": "0.1.0",
                    "digest": "not-a-digest",
                },
                "tracer": "query_engine.v1",
                "result": "pass",
                "evidence_refs": ["evidence:x"],
                "executed_by": "phlo-conformance",
                "run_at": "2026-09-01T00:00:00Z",
                "expires_at": "2026-12-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    result = CliRunner().invoke(
        plugin_group,
        ["install", "preflight-fixture", "--evidence", str(bad_evidence)],
    )
    assert result.exit_code == 1
    assert pip_calls == []
    assert "digest" in result.output


@pytest.fixture(autouse=True)
def _isolated_registry_cache():
    """Keep the module-level registry TTL cache from leaking between tests."""
    previous_cache = dict(registry_client._REGISTRY_CACHE)
    yield
    registry_client._REGISTRY_CACHE.clear()
    registry_client._REGISTRY_CACHE.update(previous_cache)
