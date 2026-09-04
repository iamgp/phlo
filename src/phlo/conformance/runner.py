"""Controller side of the artifact-bound conformance runner.

The controller never imports candidate code (isolation boundary, ADR
0053 concern 4): it inspects the candidate wheel statically, verifies
the wheel/descriptor binding, creates a disposable worker environment,
installs the exact wheel there, executes the Phlo-owned worker against
only candidate-owned entry points, and emits schema-valid
artifact-bound evidence for the run.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import re
import subprocess
import tempfile
import venv
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib import resources
from pathlib import Path
from typing import Any

from phlo.conformance.suites import RunConfig, get_suite
from phlo.plugins.trust import (
    ConformanceResultRecord,
    DescriptorRecord,
    content_digest,
)

WORKER_MODULE = "worker.py"


class ConformanceRunError(RuntimeError):
    """Raised when a conformance run cannot be completed at all."""


class ConformanceBindingError(ConformanceRunError):
    """Raised when the artifact cannot be bound to exact identities.

    Result binding to the exact wheel, descriptor, core, and suite
    identity is mandatory (issue #856: unbindable results are a STOP).
    """


@dataclass(frozen=True)
class RunOutcome:
    """The full, honest result of one conformance run."""

    suite: str
    passed: bool
    result: str
    artifact: dict[str, Any]
    specs: list[str]
    cases: list[dict[str, Any]]
    evidence: dict[str, Any]
    evidence_output: str | None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _wheel_identity(wheel: Path) -> tuple[str, str]:
    """Return (name, version) read statically from the wheel METADATA."""
    name: str | None = None
    version: str | None = None
    with zipfile.ZipFile(wheel) as archive:
        metadata_names = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_names) != 1:
            raise ConformanceBindingError(
                f"wheel {wheel.name!r} must contain exactly one .dist-info/METADATA; "
                f"found {len(metadata_names)}"
            )
        for line in archive.read(metadata_names[0]).decode("utf-8").splitlines():
            if line.startswith("Name:"):
                name = line.split(":", 1)[1].strip()
            elif line.startswith("Version:"):
                version = line.split(":", 1)[1].strip()
    if not name or not version:
        raise ConformanceBindingError(f"wheel {wheel.name!r} METADATA lacks Name/Version")
    return name, version


def _normalise(name: str) -> str:
    return name.lower().replace("_", "-")


def _worker_path() -> Path:
    resource = resources.files("phlo.conformance").joinpath(WORKER_MODULE)
    with resources.as_file(resource) as path:
        return path


def _install_wheel(venv_dir: Path, wheel: Path, *, timeout: int) -> None:
    result = subprocess.run(
        [
            str(venv_dir / "bin" / "python"),
            "-m",
            "pip",
            "install",
            "--no-input",
            "--disable-pip-version-check",
            "--no-deps",
            str(wheel.resolve()),
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise ConformanceRunError(
            f"isolated installation of {wheel.name!r} failed:\n{result.stderr or result.stdout}"
        )


def _run_worker(
    *,
    venv_dir: Path,
    workspace: Path,
    entry_point_group: str,
    suite_id: str,
    timeout: int,
) -> dict[str, Any]:
    worker_source = _worker_path()
    worker_copy = workspace / WORKER_MODULE
    worker_copy.write_text(worker_source.read_text(encoding="utf-8"), encoding="utf-8")
    result_path = workspace / "worker-result.json"
    result = subprocess.run(
        [
            str(venv_dir / "bin" / "python"),
            str(worker_copy),
            "--entry-point-group",
            entry_point_group,
            "--suite",
            suite_id,
            "--output",
            str(result_path),
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if not result_path.is_file():
        raise ConformanceRunError(
            f"conformance worker produced no result (exit {result.returncode}):\n"
            f"{result.stderr or result.stdout}"
        )
    document = json.loads(result_path.read_text(encoding="utf-8"))
    document["worker_exit_code"] = result.returncode
    document["worker_stderr"] = result.stderr
    return document


def _build_evidence(
    *,
    suite_id: str,
    passed: bool,
    descriptor: DescriptorRecord,
    wheel_digest: str,
    descriptor_digest: str,
    core_requirement: str,
    report_digest: str,
    case_results: list[dict[str, Any]],
    now: datetime,
    validity_days: int,
) -> dict[str, Any]:
    """Emit the schema-valid conformance result document.

    The shape is enforced by the #855 neutral model
    (``ConformanceResultRecord``), which mirrors
    ``registry/schema/conformance-result.v1.json``: the tracer enum is
    closed and the evidence references must be non-empty. Every binding
    (wheel digest, descriptor digest, core requirement, per-case
    outcomes) is recorded in ``evidence_refs``.
    """
    case_refs = [
        f"{suite_id}:{case['spec']}:{case['name']}:{'pass' if case['passed'] else 'fail'}"
        for case in case_results
    ]
    record = ConformanceResultRecord.from_json(
        {
            "subject": {
                "package": descriptor.package,
                "version": descriptor.version,
                "digest": wheel_digest,
            },
            "tracer": suite_id,
            "result": "pass" if passed else "fail",
            "evidence_refs": [
                *case_refs,
                f"descriptor:{descriptor_digest}",
                f"core:{core_requirement}",
                f"report:{report_digest}",
            ],
            "executed_by": "phlo-conformance",
            "run_at": now.isoformat().replace("+00:00", "Z"),
            "expires_at": (now + timedelta(days=validity_days)).isoformat().replace("+00:00", "Z"),
        }
    )
    return {
        "subject": {
            "package": record.subject_package,
            "version": record.subject_version,
            "digest": record.subject_digest,
        },
        "tracer": record.tracer,
        "result": record.result,
        "evidence_refs": list(record.evidence_refs),
        "executed_by": record.executed_by,
        "run_at": record.run_at.isoformat().replace("+00:00", "Z"),
        "expires_at": record.expires_at.isoformat().replace("+00:00", "Z"),
    }


def _core_requirement() -> str:
    phlo_version = importlib.metadata.version("phlo")
    match = re.fullmatch(r"(\d+)\.(\d+)\.\d+", phlo_version)
    if match is None:
        raise ConformanceRunError(f"phlo version {phlo_version!r} is not major.minor.patch")
    major, minor = int(match[1]), int(match[2])
    return f"phlo=={phlo_version},<{major}.{minor + 1}"


def run_conformance(
    *,
    wheel: Path,
    descriptor: Path,
    suite_id: str,
    evidence_output: Path | None = None,
    run_config: RunConfig | None = None,
    now: datetime | None = None,
) -> RunOutcome:
    """Run one conformance suite against one exact candidate artifact.

    The candidate is installed and executed only inside a disposable
    worker environment that is removed when this function returns; the
    controller process never imports candidate code.
    """
    suite = get_suite(suite_id)
    config = run_config or RunConfig()
    now = now or datetime.now(UTC)

    wheel = wheel.resolve()
    descriptor_path = descriptor.resolve()
    if not wheel.is_file():
        raise ConformanceBindingError(f"candidate wheel does not exist: {wheel}")
    if not descriptor_path.is_file():
        raise ConformanceBindingError(f"descriptor does not exist: {descriptor_path}")

    wheel_digest = _sha256_file(wheel)
    wheel_name, wheel_version = _wheel_identity(wheel)

    descriptor_data = json.loads(descriptor_path.read_text(encoding="utf-8"))
    try:
        descriptor_record = DescriptorRecord.from_json(descriptor_data["package"], descriptor_data)
    except (KeyError, ValueError) as exc:
        raise ConformanceBindingError(f"invalid descriptor: {exc}") from exc

    if _normalise(descriptor_record.package) != _normalise(wheel_name) or (
        descriptor_record.version != wheel_version
    ):
        raise ConformanceBindingError(
            f"descriptor binds {descriptor_record.package}=={descriptor_record.version} "
            f"but the wheel is {wheel_name}=={wheel_version}; results must bind to exact "
            "artifact identities"
        )

    descriptor_digest = content_digest(descriptor_record.descriptor_claim())
    core_requirement = _core_requirement()

    with tempfile.TemporaryDirectory(prefix="phlo-conformance-") as temp:
        workspace = Path(temp)
        venv_dir = workspace / "worker-env"
        venv.create(venv_dir, with_pip=True)
        _install_wheel(venv_dir, wheel, timeout=config.pip_timeout_seconds)
        worker_report = _run_worker(
            venv_dir=venv_dir,
            workspace=workspace,
            entry_point_group=suite.entry_point_group,
            suite_id=suite.suite_id,
            timeout=config.worker_timeout_seconds,
        )

    case_results: list[dict[str, Any]] = list(worker_report.get("cases", []))
    passed = bool(worker_report.get("passed")) and worker_report.get("worker_exit_code") == 0
    report_digest = content_digest(
        {
            "suite": suite.suite_id,
            "wheel_digest": wheel_digest,
            "descriptor_digest": descriptor_digest,
            "core": core_requirement,
            "cases": case_results,
        }
    )
    evidence = _build_evidence(
        suite_id=suite.suite_id,
        passed=passed,
        descriptor=descriptor_record,
        wheel_digest=wheel_digest,
        descriptor_digest=descriptor_digest,
        core_requirement=core_requirement,
        report_digest=report_digest,
        case_results=case_results,
        now=now,
        validity_days=suite.evidence_validity_days,
    )

    evidence_output_path: str | None = None
    if evidence_output is not None:
        output = evidence_output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        evidence_output_path = str(output)

    return RunOutcome(
        suite=suite.suite_id,
        passed=passed,
        result="pass" if passed else "fail",
        artifact={
            "wheel": str(wheel),
            "wheel_sha256": wheel_digest,
            "package": wheel_name,
            "version": wheel_version,
            "descriptor_sha256": descriptor_digest,
            "core": core_requirement,
        },
        specs=list(worker_report.get("specs", [])),
        cases=case_results,
        evidence=evidence,
        evidence_output=evidence_output_path,
    )


__all__ = [
    "ConformanceBindingError",
    "ConformanceRunError",
    "RunOutcome",
    "run_conformance",
]
