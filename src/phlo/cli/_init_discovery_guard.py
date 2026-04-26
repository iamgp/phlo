"""Disable eager plugin discovery for built-in init invocations."""

from __future__ import annotations

import os
import sys

_GLOBAL_FLAGS_WITHOUT_VALUES = {"--help", "-h", "--version"}


def _root_command_name(argv: list[str]) -> str | None:
    for token in argv[1:]:
        if token in _GLOBAL_FLAGS_WITHOUT_VALUES:
            return None
        if token.startswith("-"):
            continue
        return token
    return None


def is_init_command_invocation(argv: list[str] | None = None) -> bool:
    args = sys.argv if argv is None else argv
    return _root_command_name(args) == "init"


if is_init_command_invocation():
    os.environ.setdefault("PHLO_NO_AUTO_DISCOVER", "1")
