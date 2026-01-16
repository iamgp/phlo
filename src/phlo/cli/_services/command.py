"""Backwards compatibility shim for cli._services.command.

This module has been moved to cli.infrastructure.command.
All imports are re-exported for backwards compatibility.
"""

from phlo.cli.infrastructure.command import *  # noqa: F401, F403
from phlo.cli.infrastructure.command import CommandError, run_command

__all__ = ["CommandError", "run_command"]
