"""Backwards compatibility shim for cli._services.

This module has been renamed to cli.infrastructure.
All imports are re-exported for backwards compatibility.
"""

from phlo.cli.infrastructure import *  # noqa: F401, F403
from phlo.cli.infrastructure import __all__  # noqa: F401
