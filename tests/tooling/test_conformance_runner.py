"""Artifact-bound conformance runner tests (#856, ADR 0053).

Builds the independently packaged SQLite fixture wheel and the broken
variant, runs the real `query_engine.v1` tracer end to end through the
disposable worker, and pins: exact artifact digests, isolated
installation, candidate-owned entry-point loading only, cleanup, both
passing and failing tracers, and schema-valid evidence that can never
qualify a failed artifact.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from phlo.conformance import run_conformance
from phlo.conformance.suites import (
    QUERY_ENGINE_V1,
    UnknownSuiteError,
    get_suite,
    suite_ids,
)
from phlo.plugins.trust import TrustTier, resolve_tier

ROOT = Path(__file__).parents[2]
FIXTURE_ROOT = ROOT / "tests/fixtures/conformance"
CLI_MODULE = "phlo.cli.commands.plugin.check"


def _build_wheel(fixture_dir: Path, out_dir: Path) -> Path:
    """Build one fixture wheel with the surrounding environment's tooling."""
    commands = [
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "-w",
            str(out_dir),
            str(fixture_dir),
        ],
        [
            "uv",
            "build",
            "--wheel",
            "--no-build-isolation",
            "--out-dir",
            str(out_dir),
            str(fixture_dir),
        ],
    ]
    errors: list[str] = []
    for command in commands:
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, check=False, timeout=300
            )
        except FileNotFoundError as exc:
            errors.append(f"{command[0]}: {exc}")
            continue
        if result.returncode == 0:
            wheels = list(out_dir.glob("*.whl"))
            assert len(wheels) == 1, f"expected one wheel, found {wheels}"
            return wheels[0]
        errors.append(f"{command[0]}: {result.stderr or result.stdout}")
    pytest.skip(f"no wheel builder available (tried pip, uv): {errors}")


@pytest.fixture(scope="module")
def built_wheels(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    out = tmp_path_factory.mktemp("fixture-wheels")
    wheels: dict[str, Path] = {}
    for fixture_name in ("sqlite_query_engine_fixture", "sqlite_query_engine_fixture_broken"):
        fixture_dir = FIXTURE_ROOT / fixture_name
        wheels[fixture_name] = _build_wheel(fixture_dir, out / fixture_name)
    return wheels


def _descriptor_for(wheel: Path, tmp_path: Path) -> Path:
    """Emit a matching static descriptor for the built fixture wheel."""
    stem = wheel.name.split("-")[0]
    name = stem.replace("_", "-")
    descriptor = {
        "type": "source_connectors",
        "package": name,
        "version": wheel.name.split("-")[1],
        "description": f"Descriptor for {name}",
        "author": "Conformance Fixture Author",
        "tags": ["fixture"],
    }
    path = tmp_path / f"{name}-descriptor.json"
    path.write_text(json.dumps(descriptor, indent=2) + "\n", encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


# --- Closed suite registry -------------------------------------------------------------


def test_query_engine_v1_is_the_sole_approved_suite() -> None:
    assert suite_ids() == ("query_engine.v1",)
    suite = get_suite("query_engine.v1")
    assert suite.capability_type == "query_engine"
    assert suite.entry_point_group == "phlo.plugins.resources"
    assert suite.cases == QUERY_ENGINE_V1.cases


def test_unknown_suites_are_refused() -> None:
    with pytest.raises(UnknownSuiteError):
        get_suite("query_engine.v2")
    with pytest.raises(UnknownSuiteError):
        get_suite("security.v1")


# --- Passing tracer: exact digests, isolation, cleanup ---------------------------------


def test_passing_fixture_yields_passing_artifact_bound_evidence(
    built_wheels: dict[str, Path], tmp_path: Path
) -> None:
    wheel = built_wheels["sqlite_query_engine_fixture"]
    descriptor = _descriptor_for(wheel, tmp_path)
    evidence_output = tmp_path / "evidence" / "result.json"

    outcome = run_conformance(
        wheel=wheel,
        descriptor=descriptor,
        suite_id="query_engine.v1",
        evidence_output=evidence_output,
        now=datetime(2026, 9, 4, tzinfo=UTC),
    )

    assert outcome.passed is True
    assert outcome.result == "pass"
    assert outcome.specs == ["sqlite-fixture"]
    assert {case["name"] for case in outcome.cases} == set(QUERY_ENGINE_V1.cases)
    assert all(case["passed"] for case in outcome.cases)

    # Exact digests: evidence binds the exact wheel the author gave us.
    assert outcome.artifact["wheel_sha256"] == _sha256(wheel)
    assert outcome.artifact["package"] == "phlo-conformance-fixture-sqlite"
    assert outcome.artifact["version"] == "0.1.0"
    assert outcome.evidence["subject"]["digest"] == _sha256(wheel)
    assert outcome.evidence["tracer"] == "query_engine.v1"
    assert outcome.evidence["executed_by"] == "phlo-conformance"
    assert outcome.evidence["result"] == "pass"

    written = json.loads(evidence_output.read_text(encoding="utf-8"))
    assert written == outcome.evidence


def test_evidence_document_is_schema_valid(built_wheels: dict[str, Path], tmp_path: Path) -> None:
    """The emitted evidence must validate against the frozen #855 schema."""
    wheel = built_wheels["sqlite_query_engine_fixture"]
    descriptor = _descriptor_for(wheel, tmp_path)
    outcome = run_conformance(wheel=wheel, descriptor=descriptor, suite_id="query_engine.v1")
    evidence = outcome.evidence
    assert set(evidence) == {
        "subject",
        "tracer",
        "result",
        "evidence_refs",
        "executed_by",
        "run_at",
        "expires_at",
    }
    assert set(evidence["subject"]) == {"package", "version", "digest"}
    assert evidence["tracer"] in {"query_engine.v1"}
    assert evidence["result"] in {"pass", "fail"}
    assert evidence["evidence_refs"]
    assert all(isinstance(ref, str) and ref for ref in evidence["evidence_refs"])
    assert evidence["run_at"] < evidence["expires_at"]


def test_worker_workspace_is_cleaned_up(built_wheels: dict[str, Path], tmp_path: Path) -> None:
    wheel = built_wheels["sqlite_query_engine_fixture"]
    descriptor = _descriptor_for(wheel, tmp_path)
    workspace_parent = tmp_path / "workspaces"
    workspace_parent.mkdir()
    import phlo.conformance.runner as runner_module

    original_tempdir = runner_module.tempfile.tempdir
    runner_module.tempfile.tempdir = str(workspace_parent)
    try:
        run_conformance(wheel=wheel, descriptor=descriptor, suite_id="query_engine.v1")
        assert list(workspace_parent.iterdir()) == [], "disposable worker workspace was not removed"
    finally:
        runner_module.tempfile.tempdir = original_tempdir


def test_passing_evidence_qualifies_for_conformance_tested_only(
    built_wheels: dict[str, Path], tmp_path: Path
) -> None:
    """A passing run can qualify conformance-tested — and nothing above.

    The verdict binds to the exact artifact the tracer exercised: the
    wheel's own SHA-256 digest (ADR 0053 concern 2, ADR 0050 identity
    model), supplied to the resolver as ``artifact_digest``.
    """
    wheel = built_wheels["sqlite_query_engine_fixture"]
    descriptor = _descriptor_for(wheel, tmp_path)
    outcome = run_conformance(wheel=wheel, descriptor=descriptor, suite_id="query_engine.v1")
    record = outcome.evidence
    from phlo.plugins.trust import ConformanceResultRecord

    verdict = ConformanceResultRecord.from_json(record)
    descriptor_record = json.loads(descriptor.read_text(encoding="utf-8"))
    from phlo.plugins.trust import DescriptorRecord

    parsed_descriptor = DescriptorRecord.from_json(descriptor_record["package"], descriptor_record)
    wheel_digest = outcome.artifact["wheel_sha256"]
    resolution = resolve_tier(
        parsed_descriptor,
        conformance_results=(verdict,),
        now=datetime(2026, 9, 5, tzinfo=UTC),
        artifact_digest=wheel_digest,
    )
    assert resolution.tier == TrustTier.CONFORMANCE_TESTED
    assert resolution.tier != TrustTier.RELEASE_SUPPORTED


def test_verdict_does_not_bind_without_the_exact_artifact_digest(
    built_wheels: dict[str, Path], tmp_path: Path
) -> None:
    """A wheel-digest verdict never transfers to the bare descriptor
    identity or to any other artifact (no inference across identities)."""
    wheel = built_wheels["sqlite_query_engine_fixture"]
    descriptor = _descriptor_for(wheel, tmp_path)
    outcome = run_conformance(wheel=wheel, descriptor=descriptor, suite_id="query_engine.v1")
    from phlo.plugins.trust import ConformanceResultRecord, DescriptorRecord

    verdict = ConformanceResultRecord.from_json(outcome.evidence)
    descriptor_record = json.loads(descriptor.read_text(encoding="utf-8"))
    parsed_descriptor = DescriptorRecord.from_json(descriptor_record["package"], descriptor_record)
    resolution = resolve_tier(
        parsed_descriptor,
        conformance_results=(verdict,),
        now=datetime(2026, 9, 5, tzinfo=UTC),
    )
    assert resolution.tier == TrustTier.COMMUNITY


# --- Failing tracer: fails closed -------------------------------------------------------


def test_broken_fixture_fails_closed(built_wheels: dict[str, Path], tmp_path: Path) -> None:
    wheel = built_wheels["sqlite_query_engine_fixture_broken"]
    descriptor = _descriptor_for(wheel, tmp_path)
    evidence_output = tmp_path / "broken-evidence.json"

    outcome = run_conformance(
        wheel=wheel,
        descriptor=descriptor,
        suite_id="query_engine.v1",
        evidence_output=evidence_output,
        now=datetime(2026, 9, 4, tzinfo=UTC),
    )

    assert outcome.passed is False
    assert outcome.result == "fail"
    failed_cases = {case["name"] for case in outcome.cases if not case["passed"]}
    assert "execute_error_surfaces" in failed_cases
    assert "preview_bounded_page" in failed_cases

    written = json.loads(evidence_output.read_text(encoding="utf-8"))
    assert written["result"] == "fail"


def test_failed_evidence_never_qualifies_a_tier(
    built_wheels: dict[str, Path], tmp_path: Path
) -> None:
    """A failed verdict grants nothing: no qualifying tier from a broken fixture."""
    wheel = built_wheels["sqlite_query_engine_fixture_broken"]
    descriptor = _descriptor_for(wheel, tmp_path)
    outcome = run_conformance(wheel=wheel, descriptor=descriptor, suite_id="query_engine.v1")
    from phlo.plugins.trust import ConformanceResultRecord, DescriptorRecord

    verdict = ConformanceResultRecord.from_json(outcome.evidence)
    assert verdict.result == "fail"
    descriptor_record = json.loads(descriptor.read_text(encoding="utf-8"))
    resolution = resolve_tier(
        DescriptorRecord.from_json(descriptor_record["package"], descriptor_record),
        conformance_results=(verdict,),
        now=datetime(2026, 9, 5, tzinfo=UTC),
    )
    assert resolution.tier == TrustTier.COMMUNITY


def test_mismatched_descriptor_is_refused(built_wheels: dict[str, Path], tmp_path: Path) -> None:
    """Results must bind to exact identities; a mismatched pair is unbindable."""
    wheel = built_wheels["sqlite_query_engine_fixture"]
    descriptor = _descriptor_for(wheel, tmp_path)
    mismatched = json.loads(descriptor.read_text(encoding="utf-8"))
    mismatched["version"] = "9.9.9"
    mismatched_path = tmp_path / "mismatched.json"
    mismatched_path.write_text(json.dumps(mismatched), encoding="utf-8")

    from phlo.conformance import ConformanceBindingError

    with pytest.raises(ConformanceBindingError, match="bind"):
        run_conformance(wheel=wheel, descriptor=mismatched_path, suite_id="query_engine.v1")


def test_descriptor_with_trust_fields_is_refused(
    built_wheels: dict[str, Path], tmp_path: Path
) -> None:
    wheel = built_wheels["sqlite_query_engine_fixture"]
    descriptor = _descriptor_for(wheel, tmp_path)
    escalated = json.loads(descriptor.read_text(encoding="utf-8"))
    escalated["release_supported"] = True
    escalated_path = tmp_path / "escalated.json"
    escalated_path.write_text(json.dumps(escalated), encoding="utf-8")

    from phlo.conformance import ConformanceBindingError

    with pytest.raises(ConformanceBindingError, match="invalid descriptor"):
        run_conformance(wheel=wheel, descriptor=escalated_path, suite_id="query_engine.v1")


def test_unknown_suite_refused_at_runtime(built_wheels: dict[str, Path], tmp_path: Path) -> None:
    wheel = built_wheels["sqlite_query_engine_fixture"]
    descriptor = _descriptor_for(wheel, tmp_path)
    with pytest.raises(UnknownSuiteError):
        run_conformance(wheel=wheel, descriptor=descriptor, suite_id="quality.v1")


# --- CLI mode ----------------------------------------------------------------------------


def test_cli_conformance_mode_runs_the_passing_tracer(
    built_wheels: dict[str, Path], tmp_path: Path
) -> None:
    """The acceptance command shape, exercised through Click."""
    from click.testing import CliRunner

    from phlo.cli.commands.plugin import check as check_module

    wheel = built_wheels["sqlite_query_engine_fixture"]
    descriptor = _descriptor_for(wheel, tmp_path)
    evidence_output = tmp_path / "cli-evidence.json"

    runner = CliRunner()
    result = runner.invoke(
        check_module.check_cmd,
        [
            "--conformance",
            "--artifact",
            str(wheel),
            "--descriptor",
            str(descriptor),
            "--suite",
            "query_engine.v1",
            "--evidence-output",
            str(evidence_output),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["result"] == "pass"
    assert payload["evidence"]["subject"]["digest"] == _sha256(wheel)
    assert evidence_output.is_file()


def test_cli_conformance_mode_exits_nonzero_on_broken_fixture(
    built_wheels: dict[str, Path], tmp_path: Path
) -> None:
    from click.testing import CliRunner

    from phlo.cli.commands.plugin import check as check_module

    wheel = built_wheels["sqlite_query_engine_fixture_broken"]
    descriptor = _descriptor_for(wheel, tmp_path)

    runner = CliRunner()
    result = runner.invoke(
        check_module.check_cmd,
        [
            "--conformance",
            "--artifact",
            str(wheel),
            "--descriptor",
            str(descriptor),
            "--suite",
            "query_engine.v1",
            "--evidence-output",
            str(tmp_path / "broken.json"),
            "--json",
        ],
    )
    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["result"] == "fail"


def test_cli_conformance_mode_requires_binding_options() -> None:
    from click.testing import CliRunner

    from phlo.cli.commands.plugin import check as check_module

    runner = CliRunner()
    result = runner.invoke(check_module.check_cmd, ["--conformance", "--json"])
    assert result.exit_code != 0
    assert "--artifact" in result.output
