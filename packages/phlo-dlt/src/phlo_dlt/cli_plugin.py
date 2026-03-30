"""CLI plugin for DLT workflow scaffolding.

This module provides the DltCliPlugin class that exposes DLT-specific
CLI commands to the Phlo command-line interface. It integrates the
workflow scaffolding commands into the Phlo CLI.

Key Class:
    - :class:`DltCliPlugin`: CLI command plugin for DLT workflows

Commands Exposed:
    - ``phlo workflow create``: Create new ingestion workflow scaffold

Plugin Registration:
    This plugin is discovered via entry points defined in pyproject.toml:
    - ``phlo.cli_commands``: DltCliPlugin

See Also:
    - :mod:`phlo.plugins.base`: Base plugin interfaces
    - :mod:`phlo_dlt.cli_workflow`: Workflow command implementation
    - :mod:`phlo_dlt.scaffold`: Scaffolding logic

Example:
    The plugin is auto-discovered by Phlo:
    ```bash
    # User runs through Phlo CLI
    phlo workflow create --domain weather --table observations
    ```

"""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_dlt.cli_workflow import workflow_group


class DltCliPlugin(CliCommandPlugin):
    """Expose DLT CLI command groups to the Phlo plugin system.

    CLI plugin that provides DLT-specific commands to the Phlo CLI.
    Currently exposes workflow scaffolding commands.

    Attributes:
        metadata: Static plugin metadata for CLI discovery.

    Methods:
        get_cli_commands: Return CLI command groups.

    Example:
        Auto-discovered by Phlo's plugin system:
        ```python
        from phlo_dlt.cli_plugin import DltCliPlugin
        plugin = DltCliPlugin()
        commands = plugin.get_cli_commands()
        ```

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for CLI command discovery.

        Returns:
            PluginMetadata: Static metadata for the DLT CLI plugin.

        """
        return PluginMetadata(
            name="dlt",
            version="0.1.0",
            description="Workflow scaffolding commands for DLT ingestion",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands contributed by this plugin.

        Returns:
            list[click.Command]: Registered top-level DLT CLI command groups.

        """
        return [workflow_group]
