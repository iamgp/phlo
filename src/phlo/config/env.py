"""Project environment helpers."""

from __future__ import annotations

import os
from pathlib import Path

import yaml


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
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def parse_project_config_env(path: Path) -> dict[str, str]:
    """Parse top-level ``env:`` values from ``phlo.yaml``."""
    if not path.exists():
        return {}

    try:
        config = yaml.safe_load(path.read_text()) or {}
    except (OSError, yaml.YAMLError):
        return {}

    if not isinstance(config, dict):
        return {}

    values = config.get("env", {})
    if not isinstance(values, dict):
        return {}

    return {str(key): str(value) for key, value in values.items() if isinstance(key, str)}


def load_project_env(
    project_root: Path | None = None, *, include_os: bool = True
) -> dict[str, str]:
    """Load ``phlo.yaml env:``, `.phlo/.env`, and `.phlo/.env.local`.

    Later sources override earlier sources, with OS env taking final precedence
    when requested.
    """
    root = project_root or Path(os.environ.get("PHLO_PROJECT_PATH", Path.cwd()))
    env: dict[str, str] = parse_project_config_env(root / "phlo.yaml")
    for path in (root / ".phlo" / ".env", root / ".phlo" / ".env.local"):
        env.update(parse_project_env_file(path))
    if include_os:
        env.update(os.environ)
    return env


def project_env_value(name: str, default: str | None = None) -> str | None:
    """Read a value from project env files or OS environment."""
    return load_project_env().get(name, default)
