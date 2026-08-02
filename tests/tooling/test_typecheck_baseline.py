"""Contracts for the production Python type-check ratchet."""

import importlib.util
import sys
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location(
    "typecheck_baseline",
    REPO_ROOT / "scripts" / "typecheck_baseline.py",
)
assert _spec and _spec.loader
_module = importlib.util.module_from_spec(_spec)
sys.modules["typecheck_baseline"] = _module
_spec.loader.exec_module(_module)
_module_any = cast(Any, _module)

Diagnostic = _module_any.Diagnostic
compare_diagnostics = _module_any.compare_diagnostics
discover_production_roots = _module_any.discover_production_roots
load_baseline = _module_any.load_baseline
normalise_diagnostic = _module_any.normalise_diagnostic


def test_production_inventory_covers_every_python_workspace_root() -> None:
    relative_roots = {
        path.relative_to(REPO_ROOT).as_posix() for path in discover_production_roots(REPO_ROOT)
    }

    assert "src/phlo" in relative_roots
    assert "packages/phlo-mcp/src" in relative_roots
    assert all(path.endswith("/src") or path == "src/phlo" for path in relative_roots)
    assert not any("/tests" in path or "/generated" in path for path in relative_roots)
    assert len(relative_roots) == 35


def test_normalise_diagnostic_records_stable_contract_fields() -> None:
    diagnostic = normalise_diagnostic(
        {
            "check_name": "invalid-return-type",
            "description": "invalid-return-type: Return type\n does not match returned value",
            "location": {
                "path": "src\\phlo\\example.py",
                "positions": {"begin": {"line": 12, "column": 7}},
            },
        },
        REPO_ROOT,
    )

    assert diagnostic == Diagnostic(
        rule="invalid-return-type",
        path="src/phlo/example.py",
        location="12:7",
        message="Return type does not match returned value",
    )


def test_typecheck_uses_the_locked_project_ty_version() -> None:
    script = (REPO_ROOT / "scripts" / "typecheck_baseline.py").read_text(encoding="utf-8")
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    lockfile = (REPO_ROOT / "uv.lock").read_text(encoding="utf-8")

    assert "uv" in script and "--locked" in script
    assert '"ty==0.0.29"' in pyproject
    assert 'name = "ty"\nversion = "0.0.29"' in lockfile


def test_baseline_detects_new_and_removed_diagnostics() -> None:
    existing = Diagnostic("invalid-return-type", "src/phlo/a.py", "1:1", "old")
    new = Diagnostic("invalid-assignment", "packages/phlo-mcp/src/phlo_mcp/a.py", "2:3", "new")

    additions, stale = compare_diagnostics(frozenset({new}), frozenset({existing}))

    assert additions == [new]
    assert stale == [existing]


def test_committed_baseline_is_sorted_and_includes_mcp_debt() -> None:
    baseline = load_baseline(REPO_ROOT / "typecheck-baseline.json")

    assert len(baseline) == 131
    assert any(item.path.startswith("packages/phlo-mcp/src/") for item in baseline)
