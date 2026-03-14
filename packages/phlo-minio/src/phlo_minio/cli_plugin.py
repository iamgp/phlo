"""CLI plugin for MinIO commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata

from phlo_minio.cli import minio_group


class MinioCliPlugin(CliCommandPlugin):
    """Register MinIO CLI commands."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="minio",
            version="0.1.0",
            description="CLI commands for MinIO object store access",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [minio_group]
