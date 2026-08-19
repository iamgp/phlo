#!/usr/bin/env python3
"""Run strict ty checks across every production Python package source root."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PATH_PARTS = frozenset({"__pycache__", ".venv", "generated", "test", "tests", "vendor"})


def production_roots(repo_root: Path = REPO_ROOT) -> list[Path]:
    """Return all Python package source roots, excluding non-production trees."""
    candidates = [repo_root / "src" / "phlo", *sorted((repo_root / "packages").glob("*/src"))]
    roots = []
    for root in candidates:
        relative_parts = root.relative_to(repo_root).parts
        if (
            root.is_dir()
            and not EXCLUDED_PATH_PARTS.intersection(relative_parts)
            and any(path.suffix == ".py" for path in root.rglob("*.py"))
        ):
            roots.append(root)
    return roots


def ty_command(roots: Sequence[Path], repo_root: Path = REPO_ROOT) -> list[str]:
    """Build the locked strict ty command for the supplied production roots."""
    return [
        "uv",
        "run",
        "--locked",
        "ty",
        "check",
        "--error-on-warning",
        *[str(root.relative_to(repo_root)) for root in roots],
    ]


def main() -> int:
    roots = production_roots()
    return subprocess.run(ty_command(roots), cwd=REPO_ROOT, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
