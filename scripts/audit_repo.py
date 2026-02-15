#!/usr/bin/env python3
"""Repository audit: docs structure and code size checks."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_TAIL_SECTIONS = ["Common Issues", "See Also", "Summary", "Next Steps"]

MAX_PYTHON_LOC = 500


def check_blog_sections() -> list[str]:
    """Check blog posts have required sections in correct order."""
    errors: list[str] = []
    blog_dir = REPO_ROOT / "docs" / "blog"
    if not blog_dir.exists():
        return errors

    for md in sorted(blog_dir.glob("[0-9]*.md")):
        h2_sections = re.findall(r"^## (.+)$", md.read_text(), re.MULTILINE)

        # Check required sections exist
        for required in REQUIRED_TAIL_SECTIONS:
            if required not in h2_sections:
                errors.append(f"{md.relative_to(REPO_ROOT)}: missing '## {required}'")

        # Check tail order (only among the required sections that exist)
        present = [s for s in h2_sections if s in REQUIRED_TAIL_SECTIONS]
        expected = [s for s in REQUIRED_TAIL_SECTIONS if s in present]
        if present != expected:
            errors.append(
                f"{md.relative_to(REPO_ROOT)}: wrong section order: "
                f"got {present}, expected {expected}"
            )

    return errors


def check_file_sizes() -> list[str]:
    """Check Python files don't exceed the LOC target."""
    errors: list[str] = []
    search_dirs = [REPO_ROOT / "src"]
    for pkg in sorted((REPO_ROOT / "packages").glob("*/src")):
        search_dirs.append(pkg)

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for py in search_dir.rglob("*.py"):
            if "node_modules" in py.parts or "__pycache__" in py.parts:
                continue
            loc = len(py.read_text().splitlines())
            if loc > MAX_PYTHON_LOC:
                errors.append(
                    f"{py.relative_to(REPO_ROOT)}: {loc} lines (max {MAX_PYTHON_LOC})"
                )

    return errors


def main() -> int:
    failed = False

    blog_errors = check_blog_sections()
    if blog_errors:
        print("FAIL  Blog structure")
        for e in blog_errors:
            print(f"  {e}")
        failed = True
    else:
        print("OK    Blog structure")

    size_errors = check_file_sizes()
    if size_errors:
        print(f"WARN  Oversized files ({len(size_errors)})")
        for e in sorted(size_errors):
            print(f"  {e}")
    else:
        print("OK    File sizes")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
