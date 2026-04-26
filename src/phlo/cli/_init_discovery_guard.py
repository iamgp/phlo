"""Disable eager plugin discovery for built-in init invocations."""

from __future__ import annotations

import os
import sys


def is_init_command_invocation(argv: list[str] | None = None) -> bool:
    args = sys.argv if argv is None else argv
    return "init" in args[1:]


if is_init_command_invocation():
    os.environ.setdefault("PHLO_NO_AUTO_DISCOVER", "1")
