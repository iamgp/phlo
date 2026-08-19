"""Contracts for strict production Python type checking."""

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "typecheck_python.py"
SPEC = importlib.util.spec_from_file_location("typecheck_python", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
typecheck_python = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = typecheck_python
SPEC.loader.exec_module(typecheck_python)


def test_production_roots_include_every_python_package_source():
    roots = {root.relative_to(REPO_ROOT) for root in typecheck_python.production_roots()}
    expected = {
        source.relative_to(REPO_ROOT)
        for source in (REPO_ROOT / "packages").glob("*/src")
        if any(source.rglob("*.py"))
    }

    assert Path("src/phlo") in roots
    assert roots == expected | {Path("src/phlo")}


def test_production_roots_include_mcp_source():
    assert Path("packages/phlo-mcp/src") in {
        root.relative_to(REPO_ROOT) for root in typecheck_python.production_roots()
    }


def test_typecheck_command_makes_all_diagnostics_blocking():
    command = typecheck_python.ty_command(typecheck_python.production_roots())

    assert command[:6] == ["uv", "run", "--locked", "ty", "check", "--error-on-warning"]


def test_typecheck_propagates_a_diagnostic_failure(monkeypatch):
    class Result:
        returncode = 1

    monkeypatch.setattr(typecheck_python.subprocess, "run", lambda *args, **kwargs: Result())

    assert typecheck_python.main() == 1
