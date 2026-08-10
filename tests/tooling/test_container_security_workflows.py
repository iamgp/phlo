"""Workflow contracts for the focused container-security lanes."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_container_workflows_run_validation_nightly_with_pinned_tools_and_digest_rescans() -> None:
    validation = (REPO_ROOT / ".github/workflows/container-security.yml").read_text()
    nightly = (REPO_ROOT / ".github/workflows/container-rescan.yml").read_text()
    assert "schedule:" in validation
    assert "pull_request:" in validation
    assert "branches: [main]" in validation
    assert "hadolint/hadolint@sha256:" in validation
    assert "github.event.pull_request.base.sha" in validation
    assert "github.event.pull_request.head.sha" in validation
    assert 'affected-images --base "$BASE_SHA" --head "$HEAD_SHA"' in validation
    assert "affected-images --all" in validation
    assert "container-waivers.md" in validation
    assert "docker build" not in validation
    assert "aquasec/trivy" not in validation
    assert "published-fleet" in nightly
    assert "assemble-rescan-manifest" in nightly
    assert "docker buildx imagetools inspect" in nightly
    assert "generated-service-images.json" in nightly
    assert '"$image@$digest"' in nightly
    assert "gh run download" not in nightly
    assert "docker build --" not in nightly


def test_container_security_pr_paths_cover_image_contract_inputs() -> None:
    validation = (REPO_ROOT / ".github/workflows/container-security.yml").read_text()

    for path in (
        '"packages/**"',
        '"scripts/container_security.py"',
        '"scripts/generated_image_matrix.py"',
        '"security/**"',
        '"pyproject.toml"',
        '"uv.lock"',
    ):
        assert path in validation
    assert "if: always()" in validation


def test_workflow_security_audit_is_nightly_not_a_pr_ci_gate() -> None:
    ci = (REPO_ROOT / ".github/workflows/ci.yml").read_text()
    security = (REPO_ROOT / ".github/workflows/security.yml").read_text()

    assert "make zizmor" not in ci
    assert "security / workflow hardening" in security
    assert "make zizmor" in security
