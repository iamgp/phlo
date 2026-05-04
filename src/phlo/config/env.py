"""Project environment helpers."""

from __future__ import annotations

import os
from pathlib import Path


def parse_project_env_file(path: Path) -> dict[str, str]:
    """Parse a simple dotenv file into key/value pairs."""
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key:
            values[key] = value
    return values


def load_project_env(
    project_root: Path | None = None, *, include_os: bool = True
) -> dict[str, str]:
    """Load `.phlo/.env` and `.phlo/.env.local`, with OS env taking precedence."""
    root = project_root or Path.cwd()
    env: dict[str, str] = {}
    for path in (root / ".phlo" / ".env", root / ".phlo" / ".env.local"):
        env.update(parse_project_env_file(path))
    if include_os:
        env.update(os.environ)
    return env


def project_env_value(name: str, default: str | None = None) -> str | None:
    """Read a value from project env files or OS environment."""
    return load_project_env().get(name, default)
