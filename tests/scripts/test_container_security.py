"""Focused contracts for the container waiver and scan-policy helper."""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
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


def test_affected_images_selects_exact_unique_fleet_for_all_and_broad_changes() -> None:
    expected = {
        ("phlo-api", "ghcr.io/phlohouse/phlo-api:0.7.0"),
        ("dagster", "ghcr.io/phlohouse/phlo-dagster:0.6.0"),
        ("observatory", "ghcr.io/phlohouse/phlo-observatory:0.7.0"),
    }
    all_targets = container_security.affected_images(["pyproject.toml"], REPO_ROOT)["include"]
    security_targets = container_security.affected_images(
        ["scripts/container_security.py"], REPO_ROOT
    )["include"]

    assert {(target["service"], target["image"]) for target in all_targets} == expected
    assert security_targets == all_targets


def test_published_fleet_is_derived_from_source_with_required_shared_mapping() -> None:
    assert container_security.published_fleet(REPO_ROOT) == [
        {
            "image": "ghcr.io/phlohouse/phlo-api:0.7.0",
            "services": ["phlo-api"],
        },
        {
            "image": "ghcr.io/phlohouse/phlo-dagster:0.6.0",
            "services": ["dagster", "dagster-daemon"],
        },
        {
            "image": "ghcr.io/phlohouse/phlo-observatory:0.7.0",
            "services": ["observatory"],
        },
    ]


def test_rescan_manifest_assembly_sorts_and_validates_complete_fleet() -> None:
    records = [
        {
            "image": "ghcr.io/phlohouse/phlo-observatory:0.7.0",
            "digest": "sha256:" + "c" * 64,
            "services": ["observatory"],
        },
        {
            "image": "ghcr.io/phlohouse/phlo-api:0.7.0",
            "digest": "sha256:" + "a" * 64,
            "services": ["phlo-api"],
        },
        {
            "image": "ghcr.io/phlohouse/phlo-dagster:0.6.0",
            "digest": "sha256:" + "b" * 64,
            "services": ["dagster-daemon", "dagster"],
        },
    ]

    manifest = container_security.assemble_rescan_manifest(records, REPO_ROOT)

    assert [entry["image"] for entry in manifest] == sorted(entry["image"] for entry in records)
    assert manifest[1]["services"] == ["dagster", "dagster-daemon"]


def test_rescan_manifest_rejects_incomplete_duplicate_unexpected_and_malformed_records() -> None:
    valid = [
        {
            "image": "ghcr.io/phlohouse/phlo-api:0.7.0",
            "digest": "sha256:" + "a" * 64,
            "services": ["phlo-api"],
        },
        {
            "image": "ghcr.io/phlohouse/phlo-dagster:0.6.0",
            "digest": "sha256:" + "b" * 64,
            "services": ["dagster", "dagster-daemon"],
        },
        {
            "image": "ghcr.io/phlohouse/phlo-observatory:0.7.0",
            "digest": "sha256:" + "c" * 64,
            "services": ["observatory"],
        },
    ]
    invalid_cases = {
        "missing": valid[:-1],
        "duplicate": [*valid, valid[0]],
        "unexpected": [
            *valid,
            {
                "image": "ghcr.io/phlohouse/phlo-extra:1.0.0",
                "digest": "sha256:" + "d" * 64,
                "services": ["extra"],
            },
        ],
        "bad digest": [{**valid[0], "digest": "latest"}, *valid[1:]],
        "wrong Dagster mapping": [
            valid[0],
            {**valid[1], "services": ["dagster"]},
            valid[2],
        ],
        "conflicting service": [
            valid[0],
            valid[1],
            {**valid[2], "services": ["phlo-api"]},
        ],
        "malformed": [json.loads('{"image": 1}'), *valid[1:]],
    }

    for label, records in invalid_cases.items():
        try:
            container_security.assemble_rescan_manifest(records, REPO_ROOT)
        except ValueError:
            continue
        raise AssertionError(f"{label} records were accepted")
