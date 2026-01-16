"""Workflow management commands."""

from __future__ import annotations

import click

from phlo.cli.commands.workflow.create import create_workflow_cmd


@click.group(name="workflow")
def workflow_group():
    """Manage workflows."""
    pass


workflow_group.add_command(create_workflow_cmd)

__all__ = ["workflow_group"]
