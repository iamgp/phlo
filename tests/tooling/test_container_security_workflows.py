"""Workflow contracts for the focused container-security lanes."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_container_workflows_use_pinned_tools_and_digest_rescans() -> None:
    pr = (REPO_ROOT / ".github/workflows/container-security.yml").read_text()
    nightly = (REPO_ROOT / ".github/workflows/container-rescan.yml").read_text()
    assert "hadolint/hadolint@sha256:" in pr
    assert "affected-images" in pr
    assert "container-waivers.md" in pr
    assert "docker build" not in pr
    assert "aquasec/trivy" not in pr
    assert "generated-service-images" in nightly
    assert '"$image@$digest"' in nightly
