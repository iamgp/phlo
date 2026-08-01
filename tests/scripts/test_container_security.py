"""Focused contracts for the container waiver and scan-policy helper."""

from __future__ import annotations

import datetime as dt
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "container_security", REPO_ROOT / "scripts" / "container_security.py"
)
assert _spec and _spec.loader
container_security = importlib.util.module_from_spec(_spec)
sys.modules["container_security"] = container_security
_spec.loader.exec_module(container_security)


def _waiver(**overrides: object) -> dict[str, object]:
    waiver: dict[str, object] = {
        "id": "CW-001",
        "image": "ghcr.io/phlohouse/phlo-api:1",
        "vulnerability_id": "CVE-2026-0001",
        "severity": "HIGH",
        "reachability": "not reachable",
        "rationale": "Upstream has no fix.",
        "compensating_control": "Network isolation.",
        "owner": "platform@example.test",
        "approval": "Security Team",
        "approval_date": "2026-08-01",
        "expiry_date": "2026-08-15",
        "remediation_issue": "https://example.test/issues/1",
    }
    waiver.update(overrides)
    return waiver


def test_waiver_validation_rejects_expired_long_and_duplicate_entries() -> None:
    errors = container_security.validate_waivers(
        [
            _waiver(expiry_date="2026-07-31"),
            _waiver(id="CW-002", expiry_date="2026-09-01"),
            _waiver(id="CW-003"),
        ],
        dt.date(2026, 8, 1),
    )
    assert any("expired" in error for error in errors)
    assert any("exceeds 30 days" in error for error in errors)
    assert any("duplicate active image/finding" in error for error in errors)


def test_policy_allows_only_waived_unfixed_blocking_findings() -> None:
    report = {
        "Results": [
            {
                "Vulnerabilities": [
                    {"VulnerabilityID": "CVE-2026-0001", "Severity": "HIGH", "FixedVersion": ""},
                    {
                        "VulnerabilityID": "CVE-2026-0002",
                        "Severity": "CRITICAL",
                        "FixedVersion": "2.0",
                    },
                    {"VulnerabilityID": "CVE-2026-0003", "Severity": "LOW", "FixedVersion": "2.0"},
                ]
            }
        ]
    }
    errors = container_security.apply_policy(report, "ghcr.io/phlohouse/phlo-api:1", [_waiver()])
    assert errors == ["ghcr.io/phlohouse/phlo-api:1: fixable CRITICAL CVE-2026-0002 (fixed in 2.0)"]


def test_affected_images_ignores_docs_and_selects_changed_service() -> None:
    assert container_security.affected_images(["docs/index.md"], REPO_ROOT) == {"include": []}
    targets = container_security.affected_images(
        ["packages/phlo-api/src/phlo_api/Dockerfile"], REPO_ROOT
    )["include"]
    assert targets == [
        {
            "service": "phlo-api",
            "image": "ghcr.io/phlohouse/phlo-api:0.7.0",
            "package": "packages/phlo-api",
            "context": "packages/phlo-api",
            "dockerfile": "src/phlo_api/Dockerfile",
        }
    ]
