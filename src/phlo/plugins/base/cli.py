"""CLI command plugin classes.

This module defines plugin types for extending the Phlo CLI.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import click

from phlo.plugins.base.plugin import Plugin


class CliCommandPlugin(Plugin, ABC):
    """Base class for CLI command plugins.

    These plugins contribute Click commands/groups to the `phlo` CLI at runtime.

    Intended use:
    - Capability packages (e.g., `phlo-nessie`, `phlo-openmetadata`) provide their own CLI surface.
    - `phlo` core stays lightweight and only provides the CLI glue + shared utilities.
    """

    @abstractmethod
    def get_cli_commands(self) -> list[click.Command]:
        """Return Click commands/groups to register on the root CLI."""
        raise NotImplementedError
