"""Workflow contracts for the scheduled release golden path."""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"


def test_release_golden_path_runs_only_in_nightly() -> None:
    ci = yaml.safe_load((WORKFLOW_ROOT / "ci.yml").read_text(encoding="utf-8"))
    nightly = yaml.safe_load((WORKFLOW_ROOT / "nightly.yml").read_text(encoding="utf-8"))

    assert "release-golden-path" not in ci["jobs"]
    assert ci["jobs"]["windows-release-contract"]["name"] == (
        "windows / release golden path contract"
    )
    assert nightly["jobs"]["release-golden-path"] == {
        "name": "python / release golden path",
        "runs-on": "ubuntu-latest",
        "timeout-minutes": 45,
        "steps": [
            {
                "uses": "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd",
                "with": {"persist-credentials": False},
            },
            {
                "name": "Install uv",
                "uses": "astral-sh/setup-uv@5a095e7a2014a4212f075830d4f7277575a9d098",
                "with": {"version": "0.12.1"},
            },
            {
                "name": "Run release artifact golden path",
                "run": "python3 scripts/release_golden_path.py",
            },
        ],
    }


def test_nightly_release_golden_path_keeps_dispatch_and_schedule() -> None:
    nightly = (WORKFLOW_ROOT / "nightly.yml").read_text(encoding="utf-8")

    assert "  workflow_dispatch:\n" in nightly
    assert '    - cron: "0 3 * * *"' in nightly
