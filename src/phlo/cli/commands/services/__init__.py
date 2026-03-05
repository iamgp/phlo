"""Service management commands."""

from __future__ import annotations

import click

from phlo.cli.commands.services.add import add_cmd
from phlo.cli.commands.services.init import init_cmd
from phlo.cli.commands.services.list import list_cmd
from phlo.cli.commands.services.logs import logs_cmd
from phlo.cli.commands.services.remove import remove_cmd
from phlo.cli.commands.services.reset import reset_cmd
from phlo.cli.commands.services.restart import restart_cmd
from phlo.cli.commands.services.start import start_cmd
from phlo.cli.commands.services.status import status_cmd
from phlo.cli.commands.services.stop import stop_cmd


@click.group(name="services")
def services_group():
    """Manage Phlo infrastructure services (Docker)."""


# Register all commands
services_group.add_command(init_cmd)
services_group.add_command(list_cmd)
services_group.add_command(start_cmd)
services_group.add_command(stop_cmd)
services_group.add_command(reset_cmd)
services_group.add_command(restart_cmd)
services_group.add_command(status_cmd)
services_group.add_command(add_cmd)
services_group.add_command(remove_cmd)
services_group.add_command(logs_cmd)

__all__ = ["services_group"]
