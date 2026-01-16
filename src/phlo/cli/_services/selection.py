"""Backwards compatibility shim for cli._services.selection.

This module has been moved to cli.infrastructure.selection.
All imports are re-exported for backwards compatibility.
"""

from phlo.cli.infrastructure.selection import select_services_to_install

__all__ = ["select_services_to_install"]
