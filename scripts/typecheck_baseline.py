#!/usr/bin/env python3
"""Run the production type check against its checked-in diagnostic baseline."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = REPO_ROOT / "typecheck-baseline.json"
TY_COMMAND = ("uv", "run", "--locked", "ty", "check", "--output-format=gitlab")


@dataclass(frozen=True, order=True)
class Diagnostic:
    """The machine-independent fields used to identify a ty diagnostic."""

    rule: str
    path: str
    location: str
    message: str


def discover_production_roots(repo_root: Path = REPO_ROOT) -> tuple[Path, ...]:
    """Discover all checked-in Python production source roots."""

    root_package = repo_root / "src" / "phlo"
    package_projects = {
        path.parent.name for path in (repo_root / "packages").glob("*/pyproject.toml")
    }
    package_sources = {path.parent.name for path in (repo_root / "packages").glob("*/src")}
    if package_projects != package_sources:
        missing_sources = sorted(package_projects - package_sources)
        missing_projects = sorted(package_sources - package_projects)
        raise RuntimeError(
            "Production Python source inventory is inconsistent: "
            f"missing src roots for {missing_sources!r}; "
            f"missing pyproject.toml for {missing_projects!r}"
        )
    if not root_package.is_dir():
        raise RuntimeError(f"Missing production Python source root: {root_package}")

    return (
        root_package,
        *sorted(repo_root / "packages" / name / "src" for name in package_sources),
    )


def _repository_relative_path(path: str, repo_root: Path) -> str:
    candidate = Path(path.replace("\\", "/"))
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    try:
        return candidate.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"ty diagnostic path is outside the repository: {path!r}") from exc


def _normalise_message(description: str, rule: str) -> str:
    prefix = f"{rule}:"
    message = description[len(prefix) :].lstrip() if description.startswith(prefix) else description
    return " ".join(message.split())


def normalise_diagnostic(raw: dict[str, Any], repo_root: Path = REPO_ROOT) -> Diagnostic:
    """Convert one ty GitLab diagnostic into the committed contract shape."""

    location = raw["location"]["positions"]["begin"]
    rule = str(raw["check_name"])
    return Diagnostic(
        rule=rule,
        path=_repository_relative_path(str(raw["location"]["path"]), repo_root),
        location=f"{location['line']}:{location['column']}",
        message=_normalise_message(str(raw["description"]), rule),
    )


def parse_ty_output(output: str, repo_root: Path = REPO_ROOT) -> frozenset[Diagnostic]:
    """Parse ty's GitLab JSON output into unique normalized diagnostics."""

    if not output.strip():
        return frozenset()
    payload = json.loads(output)
    if not isinstance(payload, list):
        raise ValueError("ty GitLab output must be a JSON list")
    return frozenset(normalise_diagnostic(item, repo_root) for item in payload)


def load_baseline(path: Path = BASELINE_PATH) -> frozenset[Diagnostic]:
    """Load and validate the checked-in diagnostic baseline."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("typecheck baseline must be a JSON list")
    diagnostics = frozenset(Diagnostic(**item) for item in payload)
    if len(diagnostics) != len(payload):
        raise ValueError("typecheck baseline contains duplicate diagnostics")
    if payload != [asdict(item) for item in sorted(diagnostics)]:
        raise ValueError("typecheck baseline must be sorted by rule, path, location, and message")
    return diagnostics


def compare_diagnostics(
    actual: frozenset[Diagnostic], baseline: frozenset[Diagnostic]
) -> tuple[list[Diagnostic], list[Diagnostic]]:
    """Return additions and stale baseline entries in stable order."""

    return sorted(actual - baseline), sorted(baseline - actual)


def _print_diagnostics(label: str, diagnostics: list[Diagnostic]) -> None:
    print(label, file=sys.stderr)
    for diagnostic in diagnostics:
        print(
            f"  {diagnostic.rule} {diagnostic.path}:{diagnostic.location} - {diagnostic.message}",
            file=sys.stderr,
        )


def main() -> int:
    try:
        roots = discover_production_roots()
        baseline = load_baseline()
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"typecheck baseline setup failed: {exc}", file=sys.stderr)
        return 1

    root_args = [path.relative_to(REPO_ROOT).as_posix() for path in roots]
    result = subprocess.run(
        [*TY_COMMAND, *root_args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        actual = parse_ty_output(result.stdout)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"could not parse ty diagnostics: {exc}", file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        return 1

    additions, stale = compare_diagnostics(actual, baseline)
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.returncode:
        print(f"ty check failed with exit code {result.returncode}", file=sys.stderr)
    if additions:
        _print_diagnostics("New production type diagnostics:", additions)
    if stale:
        _print_diagnostics("Stale typecheck baseline entries:", stale)
    if result.returncode or additions or stale:
        return 1

    print(f"typecheck baseline matches ({len(actual)} diagnostics)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
