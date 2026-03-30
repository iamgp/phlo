"""CLI plugin module for MinIO commands.

This module registers the MinIO CLI command group with the Phlo CLI
framework. It implements the CliCommandPlugin interface to expose
minio operations as first-class CLI commands.

Examples:
    Plugin registration in entry points:
        # In pyproject.toml:
        [project.entry-points."phlo.cli_commands"]
        minio = "phlo_minio.cli_plugin:MinioCliPlugin"

    Manual plugin instantiation:
        >>> from phlo_minio.cli_plugin import MinioCliPlugin
        >>> plugin = MinioCliPlugin()
        >>> commands = plugin.get_cli_commands()
        >>> print([cmd.name for cmd in commands])
        ['minio']

See Also:
    phlo_minio.cli: Implementation of the minio command group.
    phlo.plugins.base.CliCommandPlugin: Base plugin interface.

"""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata

from phlo_minio.cli import minio_group


class MinioCliPlugin(CliCommandPlugin):
    """CLI plugin that registers MinIO commands with the Phlo CLI.

    This plugin implements the CliCommandPlugin interface to expose
    MinIO operations through the Phlo CLI framework. It provides
    access to S3-compatible storage operations via the 'minio' command
    group.

    The plugin supports:
    - Bucket and object listing
    - Administrative operations
    - Direct mc (MinIO Client) command passthrough

    Examples:
        Plugin metadata access:
            >>> plugin = MinioCliPlugin()
            >>> plugin.metadata.name
            'minio'
            >>> plugin.metadata.version
            '0.1.0'

        Getting CLI commands:
            >>> plugin = MinioCliPlugin()
            >>> commands = plugin.get_cli_commands()
            >>> minio_cmd = commands[0]
            >>> minio_cmd.name
            'minio'

        Entry point configuration:
            # In pyproject.toml entry-points:
            minio = "phlo_minio.cli_plugin:MinioCliPlugin"

    Attributes:
        metadata: PluginMetadata containing name, version, and description.

    See Also:
        phlo_minio.cli.minio_group: The minio command group implementation.
        phlo_minio.cli.minio_ls: Bucket/object listing command.
        phlo_minio.cli.minio_admin_info: Admin info command.

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the MinIO CLI plugin.

        Returns:
            PluginMetadata: Plugin identity with name, version, and
                description for display in CLI help and plugin listings.

        Examples:
            Access metadata:
                >>> plugin = MinioCliPlugin()
                >>> meta = plugin.metadata
                >>> print(f"{meta.name} v{meta.version}")
                minio v0.1.0
                >>> print(meta.description)
                CLI commands for MinIO object store access

        Note:
            Version is independent of the main phlo-minio package version.

        """
        return PluginMetadata(
            name="minio",
            version="0.1.0",
            description="CLI commands for MinIO object store access",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return the list of CLI commands exposed by this plugin.

        Returns:
            list[click.Command]: List containing the minio command group.

        Examples:
            Retrieve commands:
                >>> plugin = MinioCliPlugin()
                >>> commands = plugin.get_cli_commands()
                >>> len(commands)
                1
                >>> commands[0].name
                'minio'
                >>> commands[0].help
                'Run MinIO client (mc) commands...'

        Note:
            The returned list contains the top-level minio command group
            which itself contains subcommands (ls, admin info, etc.).

        """
        return [minio_group]
