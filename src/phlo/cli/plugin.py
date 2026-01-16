"""Plugin Management Commands

CLI commands for managing Phlo plugins.

Provides commands to:
- List installed plugins
- Get detailed plugin information
- Validate plugin health
- Create scaffolding for new plugins

This module provides backward compatibility by re-exporting the plugin_group
from the new location at phlo.cli.commands.plugin.
"""

from __future__ import annotations

from phlo.cli.commands.plugin import plugin_group

__all__ = ["plugin_group"]
